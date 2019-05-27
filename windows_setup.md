
# Environment Setup

We utilize the CCP-project repository. As such, please clone the project at https://github.com/ccp-project/eval-scripts, and attempt to follow their setup guide. If you are having difficulty using Vagrant and/or installing dependencies (this is likely to occur on Windows), please follow the below steps.

1) Create new virtual machine using VirtualBox running Ubunutu 17.10.

- VirtualBox (https://www.virtualbox.org/wiki/Downloads)

- Ubuntu 17.10 (http://old-releases.ubuntu.com/releases/17.10/)

- Setup tutorial (https://itsfoss.com/install-linux-in-virtualbox/)

2) Replace source-urls to use old 17.10 compatible options:<br />
`sudo sed -i -e 's/us.archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
`<br /><br />
(verify all urls in /etc/apt/sources.list are now set to "old-releases")

3) Verify connected to internet:<br />
`ping google.com`

4) Updates:<br />
`sudo apt-get update`

5) Install primary dependencies:<br />
`sudo apt install git`<br />
`sudo apt install curl`

6) Clone git repo:<br />
`git clone https://github.com/ccp-project/eval-scripts.git`

7) Install dependencies:<br />
`cd eval-scripts && sudo ./ccp-system-setup.sh`

8) Verify rust nightly setup, try:<br />
`rustup update`<br /><br />
If fails, do:<br />
`curl https://sh.rustup.rs -sSf > rust.install.sh`<br />
`chmod +x ./rust.install.sh`<br />
`su -c "./rust.install.sh -y -v --default-toolchain nightly" your_username`

9) Build:<br />
`make`<br />
`cd ccp-kernel && sudo ./ccp_kernel_load ipc=0`

10) Now you can run tests per descriptions here:
https://github.com/ccp-project/eval-scripts.

Further info here https://ccp-project.github.io/guide/setup/index.html
