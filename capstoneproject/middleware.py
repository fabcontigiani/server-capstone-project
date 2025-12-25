"""
Custom middleware for serving media files in production with ASGI support.
"""
import os
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils._os import safe_join


class ASGIMediaFilesMiddleware:
    """
    Middleware to serve media files in production with ASGI compatibility.
    
    This middleware handles media file requests and returns FileResponse objects
    configured for async operation to avoid StreamingHttpResponse warnings.
    
    For production with high traffic, consider using nginx or a CDN instead.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.media_url = settings.MEDIA_URL
        self.media_root = settings.MEDIA_ROOT
    
    def __call__(self, request):
        # Only handle requests that start with MEDIA_URL
        if request.path.startswith(self.media_url):
            # Get the path relative to MEDIA_ROOT
            relative_path = request.path[len(self.media_url):]
            
            try:
                # Safely join the paths to prevent directory traversal attacks
                file_path = safe_join(self.media_root, relative_path)
                
                # Check if file exists
                if os.path.isfile(file_path):
                    # Return FileResponse which handles async properly
                    # as_attachment=False means display in browser, not download
                    return FileResponse(open(file_path, 'rb'), as_attachment=False)
                else:
                    raise Http404("Media file not found")
            except (ValueError, SuspiciousFileOperation) as e:
                # safe_join raises ValueError for invalid paths
                raise Http404("Invalid media path") from e
        
        # If not a media request, continue normal processing
        response = self.get_response(request)
        return response


# Import for the except clause
from django.core.exceptions import SuspiciousFileOperation
