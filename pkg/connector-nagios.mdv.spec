%define module  connector-nagios
%define name    vigilo-%{module}
%define version 1.0
%define release 1

Name:       %{name}
Summary:    Vigilo-Nagios connector
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2

BuildRequires:   python-setuptools

Requires:   python >= 2.5
Requires:   python-setuptools
Requires:   vigilo-common vigilo-pubsub vigilo-connector
Requires:   python-daemon
Requires:   python-twisted-words python-twisted-names wokkel

Requires(pre): rpm-helper

Buildarch:  noarch


%description
Gateway from Nagios to the Vigilo message bus (XMPP) and back to Nagios.
This application is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n %{module}

%build
make PYTHON=%{_bindir}/python

%install
rm -rf $RPM_BUILD_ROOT
make install \
	DESTDIR=$RPM_BUILD_ROOT \
	PREFIX=%{_prefix} \
	SYSCONFDIR=%{_sysconfdir} \
	LOCALSTATEDIR=%{_localstatedir} \
	PYTHON=%{_bindir}/python

# Mandriva splits Twisted
sed -i -e 's/^Twisted$/Twisted_Words/' $RPM_BUILD_ROOT%{_prefix}/lib*/python*/site-packages/vigilo_connector_nagios-*-py*.egg-info/requires.txt

# Listed explicitely in %%files as %%config:
grep -v '^%{_sysconfdir}/%{name}/' INSTALLED_FILES \
	| grep -v '^%{_sysconfdir}/sysconfig' \
	| grep -v '^%{_localstatedir}/run' \
	> INSTALLED_FILES.filtered
mv -f INSTALLED_FILES.filtered INSTALLED_FILES


%pre
%_pre_useradd %{name} %{_localstatedir}/lib/vigilo/%{module} /bin/false

%post
%_post_service %{name}

%preun
%_preun_service %{name}


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc COPYING
%dir %{_sysconfdir}/vigilo/
%config(noreplace) %{_sysconfdir}/vigilo/%{module}
%config(noreplace) %{_sysconfdir}/sysconfig/*
%attr(-,%{name},%{name}) %{_localstatedir}/run/%{name}


%changelog
* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package
