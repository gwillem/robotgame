#!/usr/bin/perl

use File::Slurp;

$data = read_file(shift);

$data =~ s/""".+?"""//sg;

$data =~ s/#.+$//mg;
$data =~ s/\n\s*\n/\n/g;

print $data;
