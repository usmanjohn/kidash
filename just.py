
@uploads.route('/select_file/<file_type>/<int:file_id>', methods=['GET'])
@login_required
def select_file(file_type, file_id):
    if file_type not in ['main', 'support']:
        flash('Invalid file type', 'error')
        return redirect(url_for('uploads.home'))

    # Clear the cache for the selected file type
    cache.delete_memoized(get_cached_file_data, file_type, current_user.id)

    # Update the session with the selected file ID
    session[f'selected_{file_type}_id'] = file_id

    # Update the cache with the new file data
    try:
        get_cached_file_data(file_type, current_user.id, file_id)
        flash(f'Successfully selected {file_type} file', 'success')
    except Exception as e:
        current_app.logger.error(f"Error updating cache: {str(e)}")
        flash('Error selecting file. Please try again.', 'danger')

    return redirect(url_for('uploads.home'))