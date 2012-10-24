"""
Adlibre Deployment Script for CentOS / EL 5/6

All commands should be idempotent
"""

from fabric.api import run, put, sudo, prefix

from fabric.contrib.files import append, comment, exists, sed

from fabric.utils import error


def get_os_major_version():
    """ Helper function to determine OS major version """
    return run("egrep -oe '[0-9]' /etc/redhat-release | head -n1")


def install_epel():
    version = int(get_os_major_version())
    if version == 5:
        sudo('rpm -Uvh http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm')
    elif version == 6:
        sudo('rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm')
    else:
        msg = "version %s unknown" % (version)
        error(msg)


def install_sudo():
    run('yum -y -q install sudo')


def install_nrpe():
    sudo('yum -y -q install nrpe')
    sudo('chkconfig nrpe on')
    sudo('yum -y -q install nagios-plugins-load nagios-plugins-disk')


def configure_nrpe(hosts):
    sudo("sed -i -e 's/^allowed_hosts.*$/allowed_hosts=%s/g' /etc/nagios/nrpe.cfg" % (hosts))
    append('/etc/nagios/nrpe.cfg', 'include_dir=/etc/nagios/nrpe.d/', use_sudo=True)


def deploy_nrpe_config():
    sudo('mkdir -p /etc/nagios/nrpe.d')
    put('nrpe.d/*', '/etc/nagios/nrpe.d/', use_sudo=True)
    sudo('mkdir -p /etc/nagios/plugins')
    put('plugins/*', '/etc/nagios/plugins/', use_sudo=True)


def install_passive_checker():
    sudo('yum -y -q install nsca-client')

    # fix perms so nagios user can send alerts from cron
    sudo('chown root:nagios /etc/nagios/send_nsca.cfg')
    sudo('chmod 660 /etc/nagios/send_nsca.cfg')

    sudo('mkdir -p /etc/nagios/passive-checker')
    put('passive-checker/*', '/etc/nagios/passive-checker/', use_sudo=True)

    # Allow nagios to read OpenVZ user_beancounters. NB for non OpenVZ hosts this is not required
    append('/etc/sudoers', 'nagios,nrpe ALL=(ALL) NOPASSWD: /bin/cat /proc/user_beancounters', use_sudo=True)

    # Install nagios cronjob
    sudo('crontab -l nagios > /tmp/nagios.cron')
    append('*/15 * * * * /etc/nagios/passive-checker/run.sh', '/tmp/nagios.cron', use_sudo=True)
    sudo('crontab nagios /tmp/nagios.cron')

