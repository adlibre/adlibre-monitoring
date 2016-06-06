"""
Adlibre Deployment Script for CentOS / EL 5/6 / Amazon AMI

All commands should be idempotent
"""

from fabric.api import env, run, put, sudo, prefix

from fabric.contrib.files import append, comment, exists, sed


def _get_os_major_version():
    """ Helper function to determine OS major version """
    if exists("/etc/system-release"):
        return "Amazon"
    else:
        return run("egrep -oe '[0-9]' /etc/redhat-release | head -n1")


def _install_epel():
    version = _get_os_major_version()
    env.warn_only = True
    if run('rpm -q epel-release').failed:
        if version == "5":
            sudo('rpm -Uvh http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm')
        elif version == "6":
            sudo('rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm')
	elif version == "7":
            print("EL 7")
        elif version == "Amazon":
            print("Amazon AMI includes EPEL")
        else:
            from fabric.utils import error
            msg = "version %s unknown" % (version)
            error(msg)


def _install_sudo():
    """ Install sudo """
    if not exists("/usr/bin/sudo"):
        run('yum -y -q install sudo')


def install_os_requirements():
    """ Install OS requirements """
    _install_sudo()
    _install_epel()


def install_nrpe():
    """ Install NRPE + plugins - active checks """
    sudo('yum -y -q install nrpe')
    sudo('chkconfig nrpe on')
    sudo('yum -y -q install nagios-plugins-load nagios-plugins-disk')


def install_nsca():
    """ Install NSCA Client - passive checks"""
    sudo('yum -y -q --enablerepo=epel install nsca-client')
    

def _configure_nrpe(nrpe_allowed_hosts):
    """ Configure NRPE to accept commands from our monitoring server """
    sudo("sed -i -e 's/^allowed_hosts.*$/allowed_hosts=%s/g' /etc/nagios/nrpe.cfg" % (nrpe_allowed_hosts))
    append('/etc/nagios/nrpe.cfg', 'include_dir=/etc/nagios/nrpe.d/', use_sudo=True)
    sudo('service nrpe restart')


def deploy_nrpe_config(nrpe_allowed_hosts):
    """ Deploy NRPE configuration """
    sudo('mkdir -p /etc/nagios/nrpe.d')
    put('nrpe.d/*', '/etc/nagios/nrpe.d/', use_sudo=True, mirror_local_mode=True)
    sudo('mkdir -p /etc/nagios/plugins')
    put('plugins/*', '/etc/nagios/plugins/', use_sudo=True, mirror_local_mode=True)
    _configure_nrpe(nrpe_allowed_hosts)


def install_passive_checker(openvz=False):
    """ Install Adlibre passive checking scripts & cron"""
    install_nsca()

    # fix perms so nagios user can send alerts from cron
    sudo('chown root:nagios /etc/nagios/send_nsca.cfg')
    sudo('chmod 660 /etc/nagios/send_nsca.cfg')

    sudo('mkdir -p /etc/nagios/passive-checker')
    put('passive-checker/*', '/etc/nagios/passive-checker/', use_sudo=True, mirror_local_mode=True)

    if openvz:
        # Allow nagios to read OpenVZ user_beancounters. NB for non OpenVZ hosts this is not required
        append('/etc/sudoers', 'nagios,nrpe ALL=(ALL) NOPASSWD: /bin/cat /proc/user_beancounters', use_sudo=True)

    # Install nagios cronjob
    sudo('crontab -l -u nagios > /tmp/nagios.cron')
    append('*/15 * * * * /etc/nagios/passive-checker/run.sh', '/tmp/nagios.cron', use_sudo=True)
    sudo('crontab -u nagios /tmp/nagios.cron && rm -f /tmp/nagios.cron')


def all(nrpe_allowed_hosts, passive_checker=False, openvz=False):
    """ Install all components """
    install_os_requirements()
    install_nrpe()
    install_nsca()
    deploy_nrpe_config(nrpe_allowed_hosts)
    
    if passive_checker:
        install_passive_checker(openvz)
