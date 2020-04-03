import usocket
import os
import gc
import machine
   
     
class OTAUpdater:

    def __init__(self, github_repo, module='', main_dir='main'):
        self.http_client = HttpClient()
        self.github_repo = github_repo.rstrip('/').replace('https://github.com', 'https://api.github.com/repos')
        self.main_dir = main_dir
        self.module = module.rstrip('/')

    def check_for_update_to_install_during_newFW_reboot(self):
        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_version()

        print('Checking version... ')
        print('\tCurrent version: ', current_version)
        print('\tLatest version: ', latest_version)
        if latest_version > current_version:
            print('New version available, will download and install on newFW reboot')
            os.mkdir(self.modulepath('newFW'))
            with open(self.modulepath('newFW/.version_on_reboot'), 'w') as versionfile:
                versionfile.write(latest_version)
                versionfile.close()


    def download_and_install_update(self, latest_version, current_version):
        try:
            for i in os.listdir(""):
                print(i)
                if i == "newFW":
                    self.rmtree(i)
                    print("Directory '%s' has been removed successfully") 
            os.mkdir("newFW")
        except Exception as e: 
            print(e) 
            print("Directory '%s' can not be removed") 
        self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)
        self.rmtree(self.modulepath(self.main_dir))
        os.rename(("rev_"+current_version), ('rev_'+latest_version))
        os.rename(self.modulepath('newFW'), self.modulepath(self.main_dir))
        print('Update installed (', latest_version, '), will reboot now')
        machine.reset()

    def apply_pending_updates_if_available(self):
        if 'newFW' in os.listdir(self.module):
            if '.version' in os.listdir(self.modulepath('newFW')):
                pending_update_version = self.get_version(self.modulepath('newFW'))
                print('Pending update found: ', pending_update_version)
                self.rmtree(self.modulepath(self.main_dir))
                os.rename(self.modulepath('newFW'), self.modulepath(self.main_dir))
                print('Update applied (', pending_update_version, '), ready to rock and roll')
            else:
                print('Corrupt pending update found, discarding...')
                self.rmtree(self.modulepath('newFW'))
        else:
            print('No pending update found')

    def download_updates_if_available(self):
        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_version()

        print('Checking version... ')
        print('\tCurrent version: ', current_version)
        print('\tLatest version: ', latest_version)
        if latest_version > current_version:
            print('Updating...')
            os.mkdir(self.modulepath('newFW'))
            self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)
            with open(self.modulepath('newFW/.version'), 'w') as versionfile:
                versionfile.write(latest_version)
                versionfile.close()
 
            return True
        return False

    def rmtree(self, directory):
        if(directory=="main/main"):
            directory="main"
            for entry in os.ilistdir(directory):
                print(entry)
    
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            if is_dir:
                self.rmtree(directory + '/' + entry[0])
            else:
                os.remove(directory + '/' + entry[0])
        os.rmdir(directory)

    def get_version(self, directory):
        for i in os.listdir(directory):
            if i[:4] == "rev_":
                return i[4:]
        return '0.0'

    def get_latest_version(self):
        version = "0.0"
        file_list = self.http_client.get(self.github_repo + '/contents/')
        for file in file_list.json():
            if file['name'][:4] == 'rev_':
                version = file['name'][4:]            
        file_list.close()
        
        return version

    def download_all_files(self, root_url, version):

        file_list = self.http_client.get(root_url)
        for file in file_list.json():
            if file['type'] == 'file':
                download_url = file['download_url']
                download_path = self.modulepath('newFW/' + file['path'].replace(self.main_dir + '/', ''))
                self.download_file(download_url.replace('refs/tags/', ''), download_path)
            elif file['type'] == 'dir':
                path = self.modulepath('newFW/' + file['path'].replace(self.main_dir + '/', ''))
                os.mkdir(path)
                self.download_all_files(root_url + '/' + file['name'], version)

        file_list.close()

    def download_file(self, url, path):
        print('\tDownloading: ', path)
        with open(path, 'w') as outfile:
            try:
                response = self.http_client.get(url)
                outfile.write(response.text)
            finally:
                response.close()
                outfile.close()
                gc.collect()

    def modulepath(self, path):
        print("path:",path)
        return self.module + '/' + path if self.module else path

class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = 'utf-8'
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)


class HttpClient:

    def request(self, method, url, data=None, json=None, headers={}, stream=None):
        try:
            proto, dummy, host, path = url.split('/', 3)
        except ValueError:
            proto, dummy, host = url.split('/', 2)
            path = ''
        if proto == 'http:':
            port = 80
        elif proto == 'https:':
            import ussl
            port = 443
        else:
            raise ValueError('Unsupported protocol: ' + proto)

        if ':' in host:
            host, port = host.split(':', 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        print(ai[0])
        ai = ai[0]

        s = usocket.socket(ai[0], ai[1], ai[2])
        try:
            s.connect(ai[-1])
            if proto == 'https:':
                s = ussl.wrap_socket(s, server_hostname=host)
            s.write(b'%s /%s HTTP/1.0\r\n' % (method, path))
            if not 'Host' in headers:
                s.write(b'Host: %s\r\n' % host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                s.write(k)
                s.write(b': ')
                s.write(headers[k])
                s.write(b'\r\n')
            # add user agent
            s.write('User-Agent')
            s.write(b': ')
            s.write('MicroPython OTAUpdater')
            s.write(b'\r\n')
            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b'Content-Type: application/json\r\n')
            if data:
                s.write(b'Content-Length: %d\r\n' % len(data))
            s.write(b'\r\n')
            if data:
                s.write(data)

            l = s.readline()
            # print(l)
            l = l.split(None, 2)
            status = int(l[1])
            reason = ''
            if len(l) > 2:
                reason = l[2].rstrip()
            while True:
                l = s.readline()
                if not l or l == b'\r\n':
                    break
                # print(l)
                if l.startswith(b'Transfer-Encoding:'):
                    if b'chunked' in l:
                        raise ValueError('Unsupported ' + l)
                elif l.startswith(b'Location:') and not 200 <= status <= 299:
                    raise NotImplementedError('Redirects not yet supported')
        except OSError:
            s.close()
            raise

        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        return resp

    def head(self, url, **kw):
        return self.request('HEAD', url, **kw)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def patch(self, url, **kw):
        return self.request('PATCH', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)
