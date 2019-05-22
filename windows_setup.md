
# Environment Setup

We utilize the CCP-project repository. As such, please clone the project at https://github.com/ccp-project/eval-scripts, and attempt to follow their setup guide. If you are having difficulty using Vagrant and/or installing dependencies (this is likely to occur on Windows), please follow the below steps.

1) Create new virtual machine using VirtualBox running Ubunutu 17.10.

- VirtualBox (https://www.virtualbox.org/wiki/Downloads)

- Ubuntu 17.10 (http://old-releases.ubuntu.com/releases/17.10/)

- Setup tutorial (https://itsfoss.com/install-linux-in-virtualbox/)

2) Replace source-urls to use old 17.10 compatible options:
```sudo sed -i -e 's/us.archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
```

(verify all urls in /etc/apt/sources.list are now set to "old-releases")

3) Verify connected to internet:

```ping google.com```

4) Updates:

```sudo apt-get update```

5) Install primary dependencies:

```
sudo apt install git```

```
sudo apt install curl```

6) Clone git repo:

```git clone https://github.com/ccp-project/eval-scripts.git```

7) Install dependencies:

```cd eval-scripts && sudo ./ccp-system-setup.sh```

8) Verify rust nightly setup, try:

```rustup update```

If fails, do:

```curl https://sh.rustup.rs -sSf > rust.install.sh```
```
chmod +x ./rust.install.sh```
```
su -c "./rust.install.sh -y -v --default-toolchain nightly" your_username```

9) Build:

```make```

```cd ccp-kernel && sudo ./ccp_kernel_load ipc=0```

10) Now you can run tests per descriptions here:
https://github.com/ccp-project/eval-scripts.

Further info here https://ccp-project.github.io/guide/setup/index.html

