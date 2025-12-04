cmake_minimum_required(VERSION 3.14)
project(CS16_Aimbot LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

add_executable(aimbot main.cpp)

target_link_libraries(aimbot user32 kernel32)