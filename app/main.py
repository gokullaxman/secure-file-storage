import os
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from .extensions import db, csrf
from .models import File
from .encryption import encrypt_file, decrypt_file

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('upload.html', files=files)

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('main.dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('main.dashboard'))
        
    if not allowed_file(file.filename):
        flash('File type not allowed. Supported: ' + ', '.join(ALLOWED_EXTENSIONS), 'error')
        return redirect(url_for('main.dashboard'))
    
    if file:
        original_filename = secure_filename(file.filename)
        # Read the file data
        file_data = file.read()
        
        # Protect against path traversals and overwrites
        timestamp = datetime.utcnow().timestamp()
        stored_filename = secure_filename(f"{current_user.id}_{timestamp}_{original_filename}.enc")
        
        try:
            # Encrypt the file
            encrypted_data = encrypt_file(file_data)
        except Exception as e:
            current_app.logger.error(f"Encryption error: {e}")
            flash('Error encrypting file. Check server configuration.', 'error')
            return redirect(url_for('main.dashboard'))
            
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
        except IOError as e:
            current_app.logger.error(f"File save error: {e}")
            flash('Error saving file to disk.', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Save to db
        new_file = File(user_id=current_user.id, original_filename=original_filename, stored_filename=stored_filename)
        db.session.add(new_file)
        db.session.commit()
        
        flash('File successfully uploaded and encrypted.', 'success')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.user_id != current_user.id:
        current_app.logger.warning(f"Unauthorized download attempt by user {current_user.id} for file {file_id}")
        abort(403)
        
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_record.stored_filename)
    if not os.path.exists(filepath):
        flash('File not found on server.', 'error')
        return redirect(url_for('main.dashboard'))
        
    try:
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
    except IOError as e:
        current_app.logger.error(f"File read error: {e}")
        flash('Error reading file from disk.', 'error')
        return redirect(url_for('main.dashboard'))
        
    try:
        decrypted_data = decrypt_file(encrypted_data)
    except Exception as e:
        current_app.logger.error(f"Decryption error on {filepath}: {e}")
        flash('Error decrypting file. File may be corrupted or key changed.', 'error')
        return redirect(url_for('main.dashboard'))
        
    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=file_record.original_filename
    )

@main_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.user_id != current_user.id:
        current_app.logger.warning(f"Unauthorized delete attempt by user {current_user.id} for file {file_id}")
        abort(403)
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_record.stored_filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            current_app.logger.error(f"Error removing file {filepath}: {e}")
            flash('Error removing file from disk. Database record deleted.', 'error')
        
    db.session.delete(file_record)
    db.session.commit()
    flash('File deleted.', 'success')
    return redirect(url_for('main.dashboard'))
