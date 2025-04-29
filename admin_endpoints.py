"""
Admin Endpoints for Storybook Generator
-------------------------------------
Simple endpoints for administrative purposes.
Add this code to app.py to implement.
"""

@app.route('/admin/users')
def admin_users():
    """Admin endpoint to view all user data.
    
    This is a simple endpoint that shows all users who have accessed the application.
    In a production environment, you would add proper authentication.
    """
    # Simple admin password protection (replace with proper auth in production)
    admin_key = request.args.get('key')
    if not admin_key or admin_key != 'admin123':
        return "Unauthorized", 401
    
    # Get all users
    users_data = get_all_users()
    
    # Format timestamps for display
    users = []
    for user in users_data:
        # Clone the user data
        formatted_user = user.copy()
        
        # Format the timestamp
        timestamp = user.get('timestamp', '')
        if timestamp:
            try:
                # Parse ISO format and convert to more readable format
                dt = datetime.fromisoformat(timestamp)
                formatted_user['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                formatted_user['formatted_time'] = timestamp
        else:
            formatted_user['formatted_time'] = 'Unknown'
            
        users.append(formatted_user)
    
    # Render template
    return render_template('admin_users.html', users=users)
