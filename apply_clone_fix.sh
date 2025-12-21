#!/bin/bash

# Fix for CLONE button streaming issue
# This script adds streaming support for the clone action

API_FILE="/home/ubuntu/ai-swautomorph/src/routes/api_routes.py"

# Create backup
cp "$API_FILE" "$API_FILE.backup"

# Add streaming support after the clone operation
sed -i '/if status == '\''failed'\'':/,/return jsonify.*400/a\
                \
                # Check if streaming is requested for clone\
                stream_output = data.get('\''stream'\'', False)\
                if stream_output:\
                    # Return streaming response for clone\
                    def generate_clone_response():\
                        import json\
                        yield f"data: {json.dumps({'\''chunk'\'': f'\''Clone completed successfully for {app_name}'\''})}\\n\\n"\
                        yield f"data: {json.dumps({'\''chunk'\'': f'\''Repository cloned to: {deployment_path}'\''})}\\n\\n"\
                        yield f"data: {json.dumps({'\''chunk'\'': command_output})}\\n\\n"\
                        yield f"data: {json.dumps({'\''done'\'': True, '\''success'\'': True})}\\n\\n"\
                    \
                    return Response(stream_with_context(generate_clone_response()), mimetype='\''text/event-stream'\'',\
                                   headers={'\''Cache-Control'\'': '\''no-cache'\'', '\''X-Accel-Buffering'\'': '\''no'\''})\
' "$API_FILE"

echo "Clone streaming fix applied to $API_FILE"
echo "Backup saved as $API_FILE.backup"