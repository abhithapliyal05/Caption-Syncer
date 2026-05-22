#include <iostream>
#include <string>
#include <cstdlib> 
#include <fstream>
#include <chrono>
#include <thread>
#include <vector>

using namespace std;

int main() {
    // 1. Setup Environment Paths
    const string BASE_DIR = "C:\\Projects\\";

    string ffmpegPath = BASE_DIR + "bin\\ffmpeg.exe";
    string ffplayPath = BASE_DIR + "bin\\ffplay.exe";
    string sandboxPython = BASE_DIR + "env\\Scripts\\python.exe";
    string alignScript = BASE_DIR + "Caption-Project\\align.py";

    // 2. Get Video Input
    string videoName;
    cout << "Enter the video filename (e.g., clip.mp4): ";
    cin >> videoName;
    cin.ignore();

    // 3. Prompt for Script or Raw Extraction
    cout << "\nDo you want to provide a custom text script for precision alignment? (y/n): ";
    char scriptChoice;
    cin >> scriptChoice;
    cin.ignore();

    string modeFlag = "raw";
    string cleanText = "";

    if (scriptChoice == 'y' || scriptChoice == 'Y') {
        modeFlag = "align";

        cout << "\nPaste or type the exact script/subtitles here.\n";
        cout << "(When finished, press Enter on an empty line to start processing):\n";
        cout << "----------------------------------------------------------------\n";

        string line;
        while (getline(cin, line)) {
            if (line.empty()) break;
            cleanText += line + " ";
        }

        if (cleanText.empty()) {
            cout << "ERROR: You selected alignment but didn't enter any subtitle text!" << endl;
            return 1;
        }
    }
    else {
        cout << "\nSkipping custom script. Proceeding with raw AI transcription...\n";
    }

    // 4. Update operational target files to route into the \workspace\ folder
    string inputPath = BASE_DIR + "workspace\\" + videoName;
    string tempWav = BASE_DIR + "workspace\\" + videoName + "_temp.wav";
    string tempTxt = BASE_DIR + "workspace\\script_temp.txt";
    string srtOutput = tempWav + ".srt";

    // Clear old files from workspace
    remove(tempWav.c_str());
    remove(tempTxt.c_str());
    remove(srtOutput.c_str());

    // Write the user's pasted script to a temp file ONLY if alignment mode is active
    if (modeFlag == "align") {
        ofstream scriptOut(tempTxt);
        scriptOut << cleanText;
        scriptOut.close();
    }

    // STAGE 1: Extract Audio
    cout << "\n[1/2] Extracting audio track from video..." << endl;
    string ffmpegCmd = ffmpegPath + " -i \"" + inputPath +
        "\" -ar 16000 -ac 1 -y \"" + tempWav + "\" -loglevel quiet";

    if (system(ffmpegCmd.c_str()) != 0) {
        cout << "ERROR: FFmpeg extraction failed." << endl;
        return 1;
    }

    // STAGE 2: Run WhisperX Pipeline with Mode Flags
    cout << "[2/2] Launching WhisperX Pipeline..." << endl;
    string pythonCmd = sandboxPython + " \"" + alignScript + "\" \"" + tempWav + "\" \"" + tempTxt + "\" \"" + srtOutput + "\" --mode " + modeFlag;

    int alignResult = system(pythonCmd.c_str());

    if (alignResult == 0) {
        this_thread::sleep_for(chrono::milliseconds(100));

        cout << "\nLaunching Video Player with Framelock Subtitles..." << endl;

        string workspaceDir = "C:\\Projects\\workspace";
        string localSrt = videoName + "_temp.wav.srt";

        // Chaining directory shifts and execution flags to render cleanly inside the workspace
        string videoCmd = "cd /d \"" + workspaceDir + "\" && \"" + ffplayPath +
            "\" -i \"" + videoName +
            "\" -vf \"subtitles='" + localSrt + "':force_style='Alignment=2,FontSize=20'\" " +
            " -sn -autoexit -framedrop -loglevel error";

        system(videoCmd.c_str());
    }

    cout << "\nPress Enter to exit...";
    cin.get();
    return 0;
}
