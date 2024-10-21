# Autogen usage in a team based game
Autogen is a tool owned by Microsoft, the game environment is owned by the developpers of the forked repository.

## Install
Install Autogen as explained [here](https://github.com/microsoft/autogen?tab=readme-ov-file#quickstart).

Install the paper package as a developper, from `/initial_paper`

## Report

### Overview and objectives

The game we are considering takes place in a discrete environment, which can be modeled as a graph where the nodes represent rooms and the edges represent the corridors connecting these rooms. The objective is to locate and defuse bombs placed in various rooms using agents. These agents can perform actions such as moving between rooms, inspecting rooms, and defusing portions of the bomb's sequence. The bombs are sequential, meaning that their defusal must follow a specific order and may require the use of multiple tools—each of a different color—to be properly defused.

The referenced paper demonstrated that teams of LLM-based agents perform well on this type of problem, exhibiting a high level of reasoning (see paper for details). 

Our goal is to introduce Autogen as a more versatile and less hardcoded solution, with the aim of improving performance and addressing a wider range of scenarios.

### Methodology

We iteratively implemented various layers of Autogen built-ins to make the experiment as flexible as possible, compared to the more restrictive setup in the initial paper.

The first layer involves a group chat composed of three agents, a user proxy, all overseen by a chat manager. In this configuration, the first agent to speak often assumes leadership and directs the other agents' actions. The user proxy is responsible for both initiating the conversation with information relevant to the game state and terminating the chat when necessary.

The next step introduces a team manager within the group chat. The team manager's role is to assume leadership from the agents and ensure that all agents deliberate before selecting their actions.

The third one is to add 

## QoL
Add docker the docker group to run docker without sudo :

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
- Check the permissions of the Docker socket (/var/run/docker.sock) :
```sh
ls -l /var/run/docker.sock
```
Sould provide a result similar to :
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