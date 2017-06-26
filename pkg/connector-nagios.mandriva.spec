%define module  @SHORT_NAME@

Name:       vigilo-%{module}
Summary:    @SUMMARY@
Version:    @VERSION@
Release:    @RELEASE@%{?dist}
Source0:    %{name}-%{version}.tar.gz
URL:        @URL@
Group:      Applications/System
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

BuildRequires:   python-setuptools
BuildRequires:   python-babel

Requires:   python >= 2.5
Requires:   python-setuptools
Requires:   vigilo-connector
Requires:   nagios

Requires(pre): rpm-helper


%description
@DESCRIPTION@
This application is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q

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
%_pre_useradd vigilo-nagios %{_localstatedir}/lib/vigilo/%{module} /bin/false
%_pre_groupadd nagios vigilo-nagios
%_pre_groupadd vigilo-nagios nagios

%post
%_post_service %{name}
# Regenerer le dropin.cache
twistd --help > /dev/null 2>&1
chmod 644 %{python_sitelib}/twisted/plugins/dropin.cache 2>/dev/null
exit 0

%preun
%_preun_service %{name}

%postun
# Regenerer le dropin.cache
twistd --help > /dev/null 2>&1
chmod 644 %{python_sitelib}/twisted/plugins/dropin.cache 2>/dev/null
exit 0

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
* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr>
- initial package
