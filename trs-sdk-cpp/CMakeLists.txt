cmake_minimum_required(VERSION 3.20)
project(trs_sdk_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(trs_sdk_cpp src/trs_client.cpp)
target_include_directories(trs_sdk_cpp PUBLIC include)

