#!/bin/bash

svn export https://svn.spraakdata.gu.se/sb-arkiv/material/Makefile.rules --force
svn export https://svn.spraakdata.gu.se/sb-arkiv/material/Makefile.config --force
svn export https://svn.spraakdata.gu.se/sb-arkiv/material/Makefile.langs --force

make
