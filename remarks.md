# Install

## QoL
Add docker the docker group to run docker without sudo

```sh
sudo usermod -aG docker $USER
```

To switch display between cpu and gpu, use :
```sh
sudo prime-select nvidia / intel
```
## Troubleshooting
List of the problems encountered and how to fix them :
### Error 1
```sh
DockerException: Error while fetching server API version: ('Connection aborted.', PermissionError(13, 'Permission denied'))
```
Run the test_docker4autogen.py to check if it works after each fix. Rebooting might help after each step but shouldn't be mandatory.
- Check the permissions of the Docker socket (/var/run/docker.sock):
```sh
ls -l /var/run/docker.sock
```
Sould provide a result similar to 
```sh
srw-rw---- 1 root docker 0 Jul  8 10:20 /var/run docker.sock
```
- Try running 

```sh
sudo chgrp docker /lib/systemd/system/docker.socket
sudo chmod g+w /lib/systemd/system/docker.socket
```

This fix originated from attempting to run Autogen, encountering the error, and then examining the builder that failed on Docker. Updating the permissions seems to have resolved the issue durably.

### Error 2
```sh
UserWarning: CUDA initialization: CUDA unknown error - this may be due to an incorrectly set up environment, e.g. changing env variable CUDA_VISIBLE_DEVICES after program start.
```

This is caused by waking the computer from its "suspend" status. Rebooting fixes it.

### Error 3
```sh
ImportError: cannot import name 'packaging' from 'pkg_resources'
```
This is caused by a version of setuptools, reverting to 69.5.1 fixes it :
```sh
pip install setuptools==69.5.1
```
# Usage

## Async calls notebook
Works as intendeed with:
- gpt-3.5-turbo (20b)
- gpt-4-turbo
Does not with: 
- mistral 7b
- llama2 7b
- gpt-4 (costs a lot of money, do NOT use)