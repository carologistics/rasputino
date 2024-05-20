# needrestart - Restart daemons after library updates - Ubuntu backend
#
# Authors:
#   Thomas Liske <thomas@fiasko-nw.net>
#   Simon Chopin <simon.chopin@canonical.com>
#
# Copyright Holder:
#   2013 - 2022 (C) Thomas Liske [http://fiasko-nw.net/~thomas/]
#   2024 (C) Canonical Ltd
#
# License:
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this package; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#

package NeedRestart::UI::Ubuntu;

use strict;
use warnings;

use parent qw(NeedRestart::UI);
use NeedRestart qw(:ui);

use Locale::TextDomain 'needrestart';

needrestart_ui_register(__PACKAGE__, 0);

use constant {
    REBOOT_FILE => '/run/reboot-required'
};

sub _write_reboot_file {
    my $self = shift;
    my $output = shift;

    open(my $out_fd, '>', REBOOT_FILE);
    print $out_fd "*** " . __("System restart required") . " ***\n";
    print $out_fd $output;
    close($out_fd);
}

sub _announce {
    my $self = shift;
    my $message = shift;
    my %vars = @_;

    my $output = __x("Pending kernel upgrade!\nRunning kernel version:\n  {kversion}\nDiagnostics:\n  {message}\n",
					 kversion => $vars{KVERSION},
					 message => $message,
		   );
    $self->_write_reboot_file($output);

    $self->wprint(\*STDOUT, '', '', "\n" . $output . __"\nRestarting the system to load the new kernel will not be handled automatically, so you should consider rebooting.\n");
}


sub announce_abi {
    my $self = shift;
    my %vars = @_;

    $self->_announce(__ 'The currently running kernel has an ABI compatible upgrade pending.', %vars);
}


sub announce_ver {
    my $self = shift;
    my %vars = @_;

    $self->_announce(__x("The currently running kernel version is not the expected kernel version {eversion}.",
			 eversion => $vars{EVERSION},
		     ), %vars);
}


sub announce_ehint {
    my $self = shift;
    my %vars = @_;

    die "This UI is supposed to be used only while in Ubuntu mode.";
}


sub announce_ucode {
    my $self = shift;
    my %vars = @_;

    my $output = __x("Pending processor microcode upgrade!\nDiagnostics:\n  The currently running processor microcode revision is {current} which is not the expected microcode revision {avail}.\n",
			 current => $vars{CURRENT},
			 avail => $vars{AVAIL},
		   );
    $self->_write_reboot_file($output);

    print "\n";
    $self->wprint(\*STDOUT, '', '', "\n" . $output . __"\nRestarting the system to load the new kernel will not be handled automatically, so you should consider rebooting.\n");
}


sub notice($$) {
    my $self = shift;
    my $out = shift;

    return unless($self->{verbosity});

    my $indent = ' ';
    $indent .= $1 if($out =~ /^(\s+)/);

    $self->wprint(\*STDOUT, '', $indent, "$out\n");
}

sub vspace {
    my $self = shift;

    return unless($self->{verbosity});

    $self->SUPER::vspace(\*STDOUT);
}


sub command {
    my $self = shift;
    my $out = shift;

    print "$out\n";
}


sub query_pkgs($$$$$$) {
    my $self = shift;
    my $out = shift;
    my $def = shift;
    my $pkgs = shift;
    my $overrides = shift;
    my $cb = shift;

    die "Interactive mode not supported by this UI.";
}

sub query_conts($$$$$$) {
    my $self = shift;

    die "Interactive mode not supported by this UI.";
}

1;
