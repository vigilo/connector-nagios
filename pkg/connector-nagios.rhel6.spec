%define module  @SHORT_NAME@

Name:       vigilo-%{module}
Summary:    @SUMMARY@
Version:    @VERSION@
Release:    @RELEASE@%{?dist}
Source0:    %{name}-%{version}@PREVERSION@.tar.gz
URL:        @URL@
Group:      Applications/System
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

BuildRequires:   python-distribute
BuildRequires:   python-babel

Requires:   python-distribute
Requires:   vigilo-common vigilo-connector
Requires:   nagios
Requires(pre): group(nagios)


# Init
Requires(pre): shadow-utils
Requires(post): chkconfig
Requires(preun): chkconfig
# This is for /sbin/service
Requires(preun): initscripts
Requires(postun): initscripts

%description
@DESCRIPTION@
This application is part of the Vigilo Project <https://www.vigilo-nms.com>

%prep
%setup -q -n %{name}-%{version}@PREVERSION@

%build

%install
rm -rf $RPM_BUILD_ROOT
make install_pkg_initd \
    DESTDIR=$RPM_BUILD_ROOT \
    PREFIX=%{_prefix} \
    SYSCONFDIR=%{_sysconfdir} \
    LOCALSTATEDIR=%{_localstatedir} \
    PYTHON=%{__python}

%find_lang %{name}


%pre
getent group vigilo-nagios >/dev/null || groupadd -r vigilo-nagios
getent passwd vigilo-nagios >/dev/null || useradd -r -g vigilo-nagios -G nagios -d %{_localstatedir}/lib/vigilo/%{module} -s /sbin/nologin vigilo-nagios
usermod -a -G vigilo-nagios nagios
exit 0

%post
/sbin/chkconfig --add %{name} || :
%{_libexecdir}/twisted-dropin-cache > /dev/null 2>&1 || :

%preun
if [ $1 = 0 ]; then
    /sbin/service %{name} stop > /dev/null 2>&1 || :
    /sbin/chkconfig --del %{name} || :
fi

%postun
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} condrestart > /dev/null 2>&1 || :
fi
%{_libexecdir}/twisted-dropin-cache > /dev/null 2>&1 || :


%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{name}.lang
%defattr(644,root,root,755)
%doc COPYING.txt
%attr(755,root,root) %{_bindir}/%{name}
%attr(755,root,root) %{_initrddir}/%{name}
%dir %{_sysconfdir}/vigilo/
%dir %{_sysconfdir}/vigilo/%{module}
%attr(640,root,vigilo-nagios) %config(noreplace) %{_sysconfdir}/vigilo/%{module}/settings.ini
%config(noreplace) %{_sysconfdir}/sysconfig/*
%{python_sitelib}/vigilo*
%{python_sitelib}/twisted*
%dir %{_localstatedir}/log/vigilo
%attr(-,vigilo-nagios,vigilo-nagios) %{_localstatedir}/log/vigilo/%{module}
%attr(-,vigilo-nagios,vigilo-nagios) %{_localstatedir}/run/%{name}
%dir %{_localstatedir}/lib/vigilo
# Permissions strictes pour éviter un problème de sécurité (cf. #1093).
%defattr(644,vigilo-nagios,vigilo-nagios,750)
%{_localstatedir}/lib/vigilo/%{module}


%changelog
* Fri Jan 21 2011 Vincent Quéméner <vincent.quemener@c-s.fr>
- Rebuild for RHEL6.

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr>
- initial package
