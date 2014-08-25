Name:		mw-scons-tools
Version:	$mw_scons_tools
Release:	1%{?dist}
Summary:	MakerBot scons tools for building

License:	Proprietary
URL:		http://www.makerbot.com/makerware
Source:	        %{name}-%{version}.tar.gz

BuildRequires:	scons >= 2.3.0
Requires:	scons >= 2.3.0
%description
MakerBot scons tools for building


%prep
%setup -q -n %{name}


%build
scons --install-prefix=%{buildroot}/%{_prefix}


%install
rm -rf %{build_root}
scons --install-prefix=%{buildroot}/%{_prefix} install

%files
%{_datarootdir}/scons/site_scons/site_tools/*


%changelog

