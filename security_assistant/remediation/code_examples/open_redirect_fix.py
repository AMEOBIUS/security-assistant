# VULNERABLE:
# return redirect(request.args.get('next'))

# SECURE:
from urllib.parse import urlparse

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return (test_url.scheme in ('http', 'https') and 
            ref_url.netloc == test_url.netloc)

next_url = request.args.get('next')
if not is_safe_url(next_url):
    abort(400)
    
return redirect(next_url)
