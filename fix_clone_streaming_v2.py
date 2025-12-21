#!/usr/bin/env python3

import re

# Read the API file
with open('/home/ubuntu/ai-swautomorph/src/routes/api_routes.py', 'r') as f:
    content = f.read()

# Find the location after "if status == 'failed':" and add streaming support with proper escaping
pattern = r"(if status == 'failed':\s+return jsonify\(\{'error': error_msg, 'logs': command_output\}\), 400)"

replacement = r"""\1
                
                # Check if streaming is requested for clone
                stream_output = data.get('stream', False)
                if stream_output:
                    # Return streaming response for clone
                    def generate_clone_response():
                        import json
                        yield f"data: {json.dumps({'chunk': f'Clone completed successfully for {app_name}'})}" + "\\n\\n"
                        yield f"data: {json.dumps({'chunk': f'Repository cloned to: {deployment_path}'})}" + "\\n\\n"
                        yield f"data: {json.dumps({'chunk': command_output})}" + "\\n\\n"
                        yield f"data: {json.dumps({'done': True, 'success': True})}" + "\\n\\n"
                    
                    return Response(stream_with_context(generate_clone_response()), mimetype='text/event-stream',
                                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})"""

# Restore from backup first
with open('/home/ubuntu/ai-swautomorph/src/routes/api_routes.py.backup', 'r') as f:
    content = f.read()

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Write the fixed content back
with open('/home/ubuntu/ai-swautomorph/src/routes/api_routes.py', 'w') as f:
    f.write(new_content)

print("Clone streaming fix applied successfully with proper f-string syntax!")