cmake_minimum_required(VERSION 3.10)
project(CaptionSyncer)

# Use C++17 for modern features
set(CMAKE_CXX_STANDARD 17)

# This tells VS to create 'caption_syncer.exe' using your main.cpp
add_executable(caption_syncer main.cpp)