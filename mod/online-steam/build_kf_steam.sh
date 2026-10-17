#!/bin/sh
# kf_steam.dll for Windows x64 (and libkf_steam.so for the Linux tests), cross-compiled with zig (pip install ziglang)
SDK=${SDK:-/tmp/claude-0/sdk165/sdk}
cd "$(dirname "$0")"
python3 -m ziglang c++ -target x86_64-windows-gnu -shared -O2 -fno-exceptions -fno-rtti -static-libgcc -I "$SDK/public" kf_steam.cpp -o build/kf_steam.dll -Wl,--out-implib,build/kf_steam.lib || exit 1
python3 -m ziglang c++ -target x86_64-linux-gnu -shared -fPIC -O2 -fno-exceptions -fno-rtti -I "$SDK/public" kf_steam.cpp -o build/libkf_steam.so -ldl || exit 1
echo built dll
# the pretend Steam API for the Linux tests (never shipped)
python3 -m ziglang c++ -target x86_64-linux-gnu -shared -fPIC -O1 -I "$SDK/public" mock/mock_steam_api.cpp -o build/libmock_steam_api.so || exit 1
echo built mock
