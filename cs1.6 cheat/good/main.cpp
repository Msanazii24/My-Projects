#include <windows.h>
#include <iostream>
using namespace std;

int main() {
    cout << "CS 1.6 ESP - NO DOWNLOADS\n";
    HWND hwnd = FindWindowA(0, "Counter-Strike");
    if (!hwnd) { cout << "Launch CS 1.6\n"; cin.get(); return 0; }

    DWORD pid; GetWindowThreadProcessId(hwnd, &pid);
    HANDLE h = OpenProcess(PROCESS_ALL_ACCESS, 0, pid);

    cout << "Attached! Waiting for spawn...\n";
    while (1) {
        DWORD local = *(DWORD*)0x539984;
        if (local && *(int*)(local+0x90) > 0) {
            cout << "SPAWNED! HP: " << *(int*)(local+0x90) << "\n";
            break;
        }
        Sleep(500);
    }

    cout << "\nENEMIES:\n";
    while (!(GetAsyncKeyState(VK_F10)&1)) {
        for (int i=1; i<=32; i++) {
            DWORD ent = *(DWORD*)(0x546204 + i*0x380);
            if (!ent || ent == *(DWORD*)0x539984) continue;
            int hp = *(int*)(ent+0x90);
            int team = *(int*)(ent+0x98);
            if (hp > 0 && team != *(int*)(*(DWORD*)0x539984 + 0x98))
                cout << "Enemy " << i << " | HP: " << hp << " | Pos: "
                     << *(float*)(ent+0x34C) << ", "
                     << *(float*)(ent+0x350) << "\n";
        }
        Sleep(200); system("cls"); cout << "CS 1.6 ESP (F10=exit)\n";
    }
    CloseHandle(h);
}