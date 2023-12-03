@echo off
title UI (ushr_qc)
rem Pre-requisites: 
rem 1. Git-Bash
rem 2. Anaconda3
rem 3. Access to BitBucket Account here for latest code: https://bitbucket.org/ushrauto/ushr_qc_ui/src/master/
rem 4. Initial cloned ushr_qc_ui repository using GitBash '''cd C:\Users\jgreener\git''' and '''git clone https://jgreenerushrauto@bitbucket.org/ushrauto/ushr_qc_ui.git'''
rem 5. Correct directory paths below for location of a.)ushr_qc_ui git b.) git-bash.exe c.) anaconda3 activate batch file
echo Pulling latest code from BitBucket through Git Bash
cd %USERPROFILE%\git\ushr_qc_ui
start "" "C:\Program Files\Git\git-bash.exe" -c "git pull origin master && git status && read -p "Take_Screen_Shot_If_RED_TEXT_Above..""
timeout 7 /nobreak > NUL 
echo Opening Anaconda3 Shell
call %USERPROFILE%\AppData\Local\Continuum\anaconda3\Scripts\activate.bat
echo Updating Environment (ushr_qc)
call conda env update -f requirements.yaml
echo Opening UI (ushr_qc)
call activate ushr_qc
call python main.py
