// kf_steam.cpp - Knight Fights Online: a small Steamworks bridge for the DELTARUNE Chapter 3 runner (build 45)
//
// GameMaker can call DLL functions whose arguments and results are doubles or strings (external_define). This DLL gives the
// Knight Hub what it needs from Steam - lobbies (rooms), invites, room codes, browsing, peer-to-peer packets - and nothing else.
//
// * It does NOT link against steam_api64.dll: it loads it at run time (from its own folder first), so a missing or
//   different Steam API never stops the game from starting; kf_init() just says why Steam is not available.
// * App ID 480 ("Spacewar", Valve's public test app): set through the SteamAppId environment variable before SteamAPI_InitFlat
//   (steam_appid.txt with 480 next to the game does the same; the installer writes both).
// * Callbacks are pumped by hand (SteamAPI_ManualDispatch_*) from kf_poll(), which GameMaker calls every step; each event
//   comes back as one short string.
// * Player IDs are Steam account IDs (32 bits: exact in a GameMaker double). Lobby IDs travel as decimal strings.
// * Room codes are 7 letters (A-Z, base 26) made from the lobby's 32-bit account part. Joining by code is a verified lookup:
//   the lobby is found (lobby list search for its "kfcode", or its data requested by the reconstructed ID) and its data is
//   checked (kfgame = kfo, the same kfcode) before anything joins it.
//
// Build (no Visual Studio needed): python -m ziglang c++ -target x86_64-windows-gnu -shared -O2 -fno-exceptions -fno-rtti
//        -I <sdk>/public kf_steam.cpp -o kf_steam.dll        (see build_kf_steam.sh)

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#define KF_API extern "C" __declspec(dllexport)
#else
#include <dlfcn.h>
#define KF_API extern "C" __attribute__((visibility("default")))
#endif

#include "steam/steam_api.h"

// ---------------------------------------------------------------- the flat API, loaded at run time
typedef int (*fn_InitFlat)(SteamErrMsg *);
typedef bool (*fn_InitOld)();
typedef void (*fn_void)();
typedef HSteamPipe (*fn_GetPipe)();
typedef void (*fn_MD_RunFrame)(HSteamPipe);
typedef bool (*fn_MD_GetNext)(HSteamPipe, CallbackMsg_t *);
typedef void (*fn_MD_Free)(HSteamPipe);
typedef bool (*fn_MD_Result)(HSteamPipe, SteamAPICall_t, void *, int, int, bool *);
typedef void *(*fn_iface)();
typedef uint64_t (*fn_User_GetSteamID)(void *);
typedef const char *(*fn_Friends_GetPersonaName)(void *);
typedef const char *(*fn_Friends_GetFriendPersonaName)(void *, uint64_t);
typedef void (*fn_Friends_InviteDialog)(void *, uint64_t);
typedef bool (*fn_Utils_Overlay)(void *);
typedef SteamAPICall_t (*fn_MM_CreateLobby)(void *, int, int);
typedef SteamAPICall_t (*fn_MM_JoinLobby)(void *, uint64_t);
typedef void (*fn_MM_LeaveLobby)(void *, uint64_t);
typedef uint64_t (*fn_MM_GetLobbyOwner)(void *, uint64_t);
typedef int (*fn_MM_GetNumMembers)(void *, uint64_t);
typedef uint64_t (*fn_MM_GetMember)(void *, uint64_t, int);
typedef bool (*fn_MM_SetData)(void *, uint64_t, const char *, const char *);
typedef const char *(*fn_MM_GetData)(void *, uint64_t, const char *);
typedef bool (*fn_MM_SetJoinable)(void *, uint64_t, bool);
typedef bool (*fn_MM_SetLimit)(void *, uint64_t, int);
typedef bool (*fn_MM_RequestData)(void *, uint64_t);
typedef void (*fn_MM_AddStringFilter)(void *, const char *, const char *, int);
typedef void (*fn_MM_AddDistanceFilter)(void *, int);
typedef void (*fn_MM_AddCountFilter)(void *, int);
typedef SteamAPICall_t (*fn_MM_RequestList)(void *);
typedef uint64_t (*fn_MM_GetLobbyByIndex)(void *, int);
typedef bool (*fn_NET_Send)(void *, uint64_t, const void *, uint32_t, int, int);
typedef bool (*fn_NET_Avail)(void *, uint32_t *, int);
typedef bool (*fn_NET_Read)(void *, void *, uint32_t, uint32_t *, uint64_t *, int);
typedef bool (*fn_NET_Accept)(void *, uint64_t);
typedef bool (*fn_NET_Close)(void *, uint64_t);
typedef bool (*fn_NET_Relay)(void *, bool);
// build 49 (optional: an older steam_api64.dll without them only loses the in-game friends list)
typedef int (*fn_Friends_GetFriendCount)(void *, int);
typedef uint64_t (*fn_Friends_GetFriendByIndex)(void *, int, int);
typedef int (*fn_Friends_GetFriendPersonaState)(void *, uint64_t);
typedef bool (*fn_Friends_GetFriendGamePlayed)(void *, uint64_t, FriendGameInfo_t *);
typedef bool (*fn_MM_InviteUser)(void *, uint64_t, uint64_t);

static struct
{
    fn_InitFlat InitFlat;
    fn_InitOld InitOld;
    fn_void Shutdown;
    fn_GetPipe GetPipe;
    fn_void MD_Init;
    fn_MD_RunFrame MD_RunFrame;
    fn_MD_GetNext MD_GetNext;
    fn_MD_Free MD_Free;
    fn_MD_Result MD_Result;
    fn_iface User, Friends, Utils, MM, NET;
    fn_User_GetSteamID User_GetSteamID;
    fn_Friends_GetPersonaName Friends_GetPersonaName;
    fn_Friends_GetFriendPersonaName Friends_GetFriendPersonaName;
    fn_Friends_InviteDialog Friends_InviteDialog;
    fn_Utils_Overlay Utils_Overlay;
    fn_MM_CreateLobby MM_CreateLobby;
    fn_MM_JoinLobby MM_JoinLobby;
    fn_MM_LeaveLobby MM_LeaveLobby;
    fn_MM_GetLobbyOwner MM_GetLobbyOwner;
    fn_MM_GetNumMembers MM_GetNumMembers;
    fn_MM_GetMember MM_GetMember;
    fn_MM_SetData MM_SetData;
    fn_MM_GetData MM_GetData;
    fn_MM_SetJoinable MM_SetJoinable;
    fn_MM_SetLimit MM_SetLimit;
    fn_MM_RequestData MM_RequestData;
    fn_MM_AddStringFilter MM_AddStringFilter;
    fn_MM_AddDistanceFilter MM_AddDistanceFilter;
    fn_MM_AddCountFilter MM_AddCountFilter;
    fn_MM_RequestList MM_RequestList;
    fn_MM_GetLobbyByIndex MM_GetLobbyByIndex;
    fn_NET_Send NET_Send;
    fn_NET_Avail NET_Avail;
    fn_NET_Read NET_Read;
    fn_NET_Accept NET_Accept;
    fn_NET_Close NET_Close;
    fn_NET_Relay NET_Relay;
    fn_Friends_GetFriendCount Friends_GetFriendCount;
    fn_Friends_GetFriendByIndex Friends_GetFriendByIndex;
    fn_Friends_GetFriendPersonaState Friends_GetFriendPersonaState;
    fn_Friends_GetFriendGamePlayed Friends_GetFriendGamePlayed;
    fn_MM_InviteUser MM_InviteUser;
} S;

#ifdef _WIN32
static HMODULE g_lib = NULL;
static void *sym(const char *n) { return g_lib ? (void *)GetProcAddress(g_lib, n) : NULL; }
#else
static void *g_lib = NULL;
static void *sym(const char *n) { return g_lib ? dlsym(g_lib, n) : NULL; }
#endif

// the first of several names that exists (interface versions differ between Steam API builds)
static void *sym_any(const char *a, const char *b, const char *c)
{
    void *p = sym(a);
    if (!p && b) p = sym(b);
    if (!p && c) p = sym(c);
    return p;
}

// ---------------------------------------------------------------- state
static int g_init = 0;              // 1 up, 0 not tried / failed
static char g_status[512] = "not started";
static HSteamPipe g_pipe = 0;
static void *g_user = NULL, *g_friends = NULL, *g_utils = NULL, *g_mm = NULL, *g_net = NULL;
static uint64_t g_me = 0;
static uint64_t g_lobby = 0;
static uint64_t g_owner = 0;
static SteamAPICall_t g_call_create = 0, g_call_join = 0, g_call_list = 0, g_call_find_list = 0;
static uint64_t g_find_id = 0;      // the lobby a code lookup waits for (RequestLobbyData)
static char g_find_code[16] = "";
static int g_find_pending = 0;      // 0 none, else how many answers are still out
static char g_found[512] = "";
static uint64_t g_last_from = 0;
static char g_str[2048];            // small string results (valid until the next call that uses it)
static char g_recv[65536 + 1];
static char g_browse[50][256];
static int g_browse_n = 0;
static char g_launch[64] = "";

#define EVQ 128
static char g_evq[EVQ][256];
static int g_ev_head = 0, g_ev_tail = 0;

static void ev(const char *s)
{
    int n = (g_ev_tail + 1) % EVQ;
    if (n == g_ev_head) return;  // full: the oldest are being read slower than they come; drop the newest
    snprintf(g_evq[g_ev_tail], sizeof(g_evq[0]), "%s", s);
    g_ev_tail = n;
}

static const uint64_t STEAMID_INDIVIDUAL = 76561197960265728ULL;   // public universe, individual, desktop instance
static const uint64_t STEAMID_LOBBY_HIGH = 0x0186000000000000ULL;  // public universe, chat, lobby + MMS lobby instance flags

static uint32_t acct_of(uint64_t sid) { return (uint32_t)(sid & 0xFFFFFFFFULL); }
static uint64_t sid_of_acct(double a) { return STEAMID_INDIVIDUAL + (uint64_t)(uint32_t)a; }

static uint64_t parse_u64(const char *s)
{
    uint64_t v = 0;
    if (!s) return 0;
    for (; *s; s++)
    {
        if (*s < '0' || *s > '9') return 0;
        v = v * 10 + (uint64_t)(*s - '0');
    }
    return v;
}

// 32-bit lobby account -> 7 letters (A-Z), most significant first; and back (0 when it is not a code)
static void code_of(uint64_t lobby, char *out)
{
    uint32_t a = acct_of(lobby);
    for (int i = 6; i >= 0; i--)
    {
        out[i] = (char)('A' + (a % 26));
        a /= 26;
    }
    out[7] = 0;
}

static int acct_from_code(const char *c, uint32_t *out)
{
    uint64_t v = 0;
    if (!c || strlen(c) != 7) return 0;
    for (int i = 0; i < 7; i++)
    {
        char ch = c[i];
        if (ch >= 'a' && ch <= 'z') ch = (char)(ch - 32);
        if (ch < 'A' || ch > 'Z') return 0;
        v = v * 26 + (uint64_t)(ch - 'A');
    }
    if (v > 0xFFFFFFFFULL) return 0;
    *out = (uint32_t)v;
    return 1;
}

static int is_member(uint64_t sid)
{
    if (!g_lobby) return 0;
    int n = S.MM_GetNumMembers(g_mm, g_lobby);
    for (int i = 0; i < n; i++)
        if (S.MM_GetMember(g_mm, g_lobby, i) == sid) return 1;
    return 0;
}

static const char *data_of(uint64_t lobby, const char *key)
{
    const char *v = S.MM_GetData(g_mm, lobby, key);
    return v ? v : "";
}

// a lobby data value copied out at once (Steam does not promise how long its returned string stays valid); '|' never
// gets through (it separates the fields we hand to the game)
static void data_copy(uint64_t lobby, const char *key, char *out, size_t cap)
{
    snprintf(out, cap, "%s", data_of(lobby, key));
    for (char *p = out; *p; p++)
        if (*p == '|') *p = '/';
}

// "id|ver|np|mx|st|name" (with_code: "id|code|name|np|mx|ver|st") of a lobby we have data for
static void lobby_line(uint64_t id, char *out, size_t cap, int with_code)
{
    char code[8], name[64], mx[16], ver[16], st[16], npd[16];
    code_of(id, code);
    data_copy(id, "name", name, sizeof(name));
    data_copy(id, "mx", mx, sizeof(mx));
    data_copy(id, "ver", ver, sizeof(ver));
    data_copy(id, "st", st, sizeof(st));
    data_copy(id, "np", npd, sizeof(npd));
    int np = S.MM_GetNumMembers(g_mm, id);
    if (np <= 0 && npd[0]) np = atoi(npd);
    if (with_code)
        snprintf(out, cap, "%llu|%s|%s|%d|%s|%s|%s", (unsigned long long)id, code, name, np, mx, ver, st);
    else
        snprintf(out, cap, "%llu|%s|%d|%s|%s|%s", (unsigned long long)id, ver, np, mx, st, name);
}

// ---------------------------------------------------------------- loading
static int load_lib(void)
{
    if (g_lib) return 1;
#ifdef _WIN32
    char path[MAX_PATH * 2];
    HMODULE self = NULL;
    // our own folder first (the installer puts steam_api64.dll next to kf_steam.dll)
    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCSTR)&load_lib, &self))
    {
        DWORD n = GetModuleFileNameA(self, path, MAX_PATH);
        if (n > 0 && n < MAX_PATH)
        {
            char *slash = strrchr(path, '\\');
            if (slash)
            {
                strcpy(slash + 1, "steam_api64.dll");
                g_lib = LoadLibraryA(path);
            }
        }
    }
    if (!g_lib) g_lib = LoadLibraryA("steam_api64.dll");
#else
    const char *p = getenv("KF_STEAM_API");
    g_lib = dlopen(p ? p : "libsteam_api.so", RTLD_NOW | RTLD_LOCAL);
#endif
    return g_lib != NULL;
}

// ---------------------------------------------------------------- init
KF_API double kf_init(void)
{
    if (g_init) return 1;
    // app 480 ("Spacewar") before steam_api64.dll is even loaded, so its own C runtime starts with it in the environment
#ifdef _WIN32
    SetEnvironmentVariableA("SteamAppId", "480");
    SetEnvironmentVariableA("SteamGameId", "480");
    _putenv_s("SteamAppId", "480");
    _putenv_s("SteamGameId", "480");
#else
    setenv("SteamAppId", "480", 1);
    setenv("SteamGameId", "480", 1);
#endif
    if (!load_lib())
    {
        snprintf(g_status, sizeof(g_status), "steam_api64.dll not found");
        return 0;
    }
    S.InitFlat = (fn_InitFlat)sym("SteamAPI_InitFlat");
    S.InitOld = (fn_InitOld)sym_any("SteamAPI_Init", "SteamAPI_InitSafe", NULL);
    S.Shutdown = (fn_void)sym("SteamAPI_Shutdown");
    S.GetPipe = (fn_GetPipe)sym("SteamAPI_GetHSteamPipe");
    S.MD_Init = (fn_void)sym("SteamAPI_ManualDispatch_Init");
    S.MD_RunFrame = (fn_MD_RunFrame)sym("SteamAPI_ManualDispatch_RunFrame");
    S.MD_GetNext = (fn_MD_GetNext)sym("SteamAPI_ManualDispatch_GetNextCallback");
    S.MD_Free = (fn_MD_Free)sym("SteamAPI_ManualDispatch_FreeLastCallback");
    S.MD_Result = (fn_MD_Result)sym("SteamAPI_ManualDispatch_GetAPICallResult");
    S.User = (fn_iface)sym_any("SteamAPI_SteamUser_v023", "SteamAPI_SteamUser_v022", "SteamAPI_SteamUser_v021");
    S.Friends = (fn_iface)sym_any("SteamAPI_SteamFriends_v018", "SteamAPI_SteamFriends_v017", NULL);
    S.Utils = (fn_iface)sym_any("SteamAPI_SteamUtils_v011", "SteamAPI_SteamUtils_v010", NULL);
    S.MM = (fn_iface)sym("SteamAPI_SteamMatchmaking_v009");
    S.NET = (fn_iface)sym("SteamAPI_SteamNetworking_v006");
    S.User_GetSteamID = (fn_User_GetSteamID)sym("SteamAPI_ISteamUser_GetSteamID");
    S.Friends_GetPersonaName = (fn_Friends_GetPersonaName)sym("SteamAPI_ISteamFriends_GetPersonaName");
    S.Friends_GetFriendPersonaName = (fn_Friends_GetFriendPersonaName)sym("SteamAPI_ISteamFriends_GetFriendPersonaName");
    S.Friends_InviteDialog = (fn_Friends_InviteDialog)sym("SteamAPI_ISteamFriends_ActivateGameOverlayInviteDialog");
    S.Utils_Overlay = (fn_Utils_Overlay)sym("SteamAPI_ISteamUtils_IsOverlayEnabled");
    S.MM_CreateLobby = (fn_MM_CreateLobby)sym("SteamAPI_ISteamMatchmaking_CreateLobby");
    S.MM_JoinLobby = (fn_MM_JoinLobby)sym("SteamAPI_ISteamMatchmaking_JoinLobby");
    S.MM_LeaveLobby = (fn_MM_LeaveLobby)sym("SteamAPI_ISteamMatchmaking_LeaveLobby");
    S.MM_GetLobbyOwner = (fn_MM_GetLobbyOwner)sym("SteamAPI_ISteamMatchmaking_GetLobbyOwner");
    S.MM_GetNumMembers = (fn_MM_GetNumMembers)sym("SteamAPI_ISteamMatchmaking_GetNumLobbyMembers");
    S.MM_GetMember = (fn_MM_GetMember)sym("SteamAPI_ISteamMatchmaking_GetLobbyMemberByIndex");
    S.MM_SetData = (fn_MM_SetData)sym("SteamAPI_ISteamMatchmaking_SetLobbyData");
    S.MM_GetData = (fn_MM_GetData)sym("SteamAPI_ISteamMatchmaking_GetLobbyData");
    S.MM_SetJoinable = (fn_MM_SetJoinable)sym("SteamAPI_ISteamMatchmaking_SetLobbyJoinable");
    S.MM_SetLimit = (fn_MM_SetLimit)sym("SteamAPI_ISteamMatchmaking_SetLobbyMemberLimit");
    S.MM_RequestData = (fn_MM_RequestData)sym("SteamAPI_ISteamMatchmaking_RequestLobbyData");
    S.MM_AddStringFilter = (fn_MM_AddStringFilter)sym("SteamAPI_ISteamMatchmaking_AddRequestLobbyListStringFilter");
    S.MM_AddDistanceFilter = (fn_MM_AddDistanceFilter)sym("SteamAPI_ISteamMatchmaking_AddRequestLobbyListDistanceFilter");
    S.MM_AddCountFilter = (fn_MM_AddCountFilter)sym("SteamAPI_ISteamMatchmaking_AddRequestLobbyListResultCountFilter");
    S.MM_RequestList = (fn_MM_RequestList)sym("SteamAPI_ISteamMatchmaking_RequestLobbyList");
    S.MM_GetLobbyByIndex = (fn_MM_GetLobbyByIndex)sym("SteamAPI_ISteamMatchmaking_GetLobbyByIndex");
    S.NET_Send = (fn_NET_Send)sym("SteamAPI_ISteamNetworking_SendP2PPacket");
    S.NET_Avail = (fn_NET_Avail)sym("SteamAPI_ISteamNetworking_IsP2PPacketAvailable");
    S.NET_Read = (fn_NET_Read)sym("SteamAPI_ISteamNetworking_ReadP2PPacket");
    S.NET_Accept = (fn_NET_Accept)sym("SteamAPI_ISteamNetworking_AcceptP2PSessionWithUser");
    S.NET_Close = (fn_NET_Close)sym("SteamAPI_ISteamNetworking_CloseP2PSessionWithUser");
    S.NET_Relay = (fn_NET_Relay)sym("SteamAPI_ISteamNetworking_AllowP2PPacketRelay");
    S.Friends_GetFriendCount = (fn_Friends_GetFriendCount)sym("SteamAPI_ISteamFriends_GetFriendCount");
    S.Friends_GetFriendByIndex = (fn_Friends_GetFriendByIndex)sym("SteamAPI_ISteamFriends_GetFriendByIndex");
    S.Friends_GetFriendPersonaState = (fn_Friends_GetFriendPersonaState)sym("SteamAPI_ISteamFriends_GetFriendPersonaState");
    S.Friends_GetFriendGamePlayed = (fn_Friends_GetFriendGamePlayed)sym("SteamAPI_ISteamFriends_GetFriendGamePlayed");
    S.MM_InviteUser = (fn_MM_InviteUser)sym("SteamAPI_ISteamMatchmaking_InviteUserToLobby");
    void **must[] = {(void **)&S.Shutdown, (void **)&S.GetPipe, (void **)&S.MD_Init, (void **)&S.MD_RunFrame, (void **)&S.MD_GetNext, (void **)&S.MD_Free,
                     (void **)&S.MD_Result, (void **)&S.User, (void **)&S.Friends, (void **)&S.Utils, (void **)&S.MM, (void **)&S.NET,
                     (void **)&S.User_GetSteamID, (void **)&S.Friends_GetPersonaName, (void **)&S.Friends_GetFriendPersonaName,
                     (void **)&S.Friends_InviteDialog, (void **)&S.Utils_Overlay, (void **)&S.MM_CreateLobby, (void **)&S.MM_JoinLobby,
                     (void **)&S.MM_LeaveLobby, (void **)&S.MM_GetLobbyOwner, (void **)&S.MM_GetNumMembers, (void **)&S.MM_GetMember,
                     (void **)&S.MM_SetData, (void **)&S.MM_GetData, (void **)&S.MM_SetJoinable, (void **)&S.MM_SetLimit, (void **)&S.MM_RequestData,
                     (void **)&S.MM_AddStringFilter, (void **)&S.MM_AddDistanceFilter, (void **)&S.MM_AddCountFilter, (void **)&S.MM_RequestList,
                     (void **)&S.MM_GetLobbyByIndex, (void **)&S.NET_Send, (void **)&S.NET_Avail, (void **)&S.NET_Read, (void **)&S.NET_Accept,
                     (void **)&S.NET_Close, (void **)&S.NET_Relay};
    for (size_t i = 0; i < sizeof(must) / sizeof(must[0]); i++)
    {
        if (!*must[i])
        {
            snprintf(g_status, sizeof(g_status), "this steam_api64.dll lacks a function Knight Fights needs (too old?)");
            return 0;
        }
    }
    if (!S.InitFlat && !S.InitOld)
    {
        snprintf(g_status, sizeof(g_status), "this steam_api64.dll has no init function");
        return 0;
    }
    // app 480 ("Spacewar"), whatever launched the game
#ifdef _WIN32
    SetEnvironmentVariableA("SteamAppId", "480");
    SetEnvironmentVariableA("SteamGameId", "480");
#else
    setenv("SteamAppId", "480", 1);
    setenv("SteamGameId", "480", 1);
#endif
    if (S.InitFlat)
    {
        SteamErrMsg err;
        memset(err, 0, sizeof(err));
        int r = S.InitFlat(&err);
        if (r != 0)
        {
            snprintf(g_status, sizeof(g_status), "%s", err[0] ? err : "Steam is not running or not signed in");
            return -1;
        }
    }
    else if (!S.InitOld())
    {
        snprintf(g_status, sizeof(g_status), "Steam is not running or not signed in");
        return -1;
    }
    S.MD_Init();
    g_pipe = S.GetPipe();
    g_user = S.User();
    g_friends = S.Friends();
    g_utils = S.Utils();
    g_mm = S.MM();
    g_net = S.NET();
    if (!g_user || !g_friends || !g_utils || !g_mm || !g_net)
    {
        snprintf(g_status, sizeof(g_status), "Steam interfaces missing");
        S.Shutdown();
        return -2;
    }
    S.NET_Relay(g_net, true);
    g_me = S.User_GetSteamID(g_user);
    g_init = 1;
    snprintf(g_status, sizeof(g_status), "ok");
    // started from a Steam invite: "+connect_lobby <id>" on the command line
#ifdef _WIN32
    const char *cl = GetCommandLineA();
#else
    const char *cl = getenv("KF_CMDLINE");
#endif
    if (cl)
    {
        const char *p = strstr(cl, "+connect_lobby");
        if (p)
        {
            p += strlen("+connect_lobby");
            while (*p == ' ' || *p == '"') p++;
            int i = 0;
            while (p[i] >= '0' && p[i] <= '9' && i < 30) { g_launch[i] = p[i]; i++; }
            g_launch[i] = 0;
        }
    }
    return 1;
}

KF_API const char *kf_status(void) { return g_status; }

KF_API double kf_shutdown(void)
{
    if (!g_init) return 0;
    if (g_lobby) S.MM_LeaveLobby(g_mm, g_lobby);
    g_lobby = 0;
    S.Shutdown();
    g_init = 0;
    return 1;
}

KF_API double kf_my_acct(void) { return g_init ? (double)acct_of(g_me) : 0; }

KF_API const char *kf_my_name(void)
{
    if (!g_init) return "";
    const char *n = S.Friends_GetPersonaName(g_friends);
    snprintf(g_str, sizeof(g_str), "%s", n ? n : "");
    return g_str;
}

KF_API const char *kf_name(double acct)
{
    if (!g_init) return "";
    const char *n = S.Friends_GetFriendPersonaName(g_friends, sid_of_acct(acct));
    snprintf(g_str, sizeof(g_str), "%s", n ? n : "");
    return g_str;
}

// ---------------------------------------------------------------- lobbies
// type: 0 private, 1 friends only, 2 public (ELobbyType: private 0, friends 1, public 2)
KF_API double kf_lobby_create(double type, double max)
{
    if (!g_init) return 0;
    int t = (int)type;
    if (t < 0 || t > 2) t = 1;
    int mx = (int)max;
    if (mx < 2) mx = 2;
    if (mx > 8) mx = 8;
    if (g_lobby) { S.MM_LeaveLobby(g_mm, g_lobby); g_lobby = 0; }
    g_call_create = S.MM_CreateLobby(g_mm, t, mx);
    return g_call_create != 0;
}

KF_API double kf_lobby_join_id(const char *id)
{
    if (!g_init) return 0;
    uint64_t l = parse_u64(id);
    if (!l) return 0;
    if (g_lobby && g_lobby != l) { S.MM_LeaveLobby(g_mm, g_lobby); g_lobby = 0; }
    g_call_join = S.MM_JoinLobby(g_mm, l);
    return g_call_join != 0;
}

// the code -> a lobby: two lookups at once (the lobby list, for public rooms; the reconstructed ID's data, for the rest),
// the first that finds a Knight Fights lobby with this code answers "found:<id>|<ver>|<np>|<mx>|<st>|<name>", else "notfound"
KF_API double kf_lobby_find(const char *code)
{
    if (!g_init) return 0;
    uint32_t a = 0;
    if (!acct_from_code(code, &a)) return 0;
    snprintf(g_find_code, sizeof(g_find_code), "%s", code);
    for (char *p = g_find_code; *p; p++) if (*p >= 'a' && *p <= 'z') *p = (char)(*p - 32);
    g_find_id = STEAMID_LOBBY_HIGH | (uint64_t)a;
    g_find_pending = 0;
    g_found[0] = 0;
    if (S.MM_RequestData(g_mm, g_find_id)) g_find_pending++;
    S.MM_AddStringFilter(g_mm, "kfcode", g_find_code, k_ELobbyComparisonEqual);
    S.MM_AddDistanceFilter(g_mm, k_ELobbyDistanceFilterWorldwide);
    S.MM_AddCountFilter(g_mm, 5);
    g_call_find_list = S.MM_RequestList(g_mm);
    if (g_call_find_list) g_find_pending++;
    if (!g_find_pending) { ev("notfound"); return 0; }
    return 1;
}

// an invite's lobby: its data first (the version check), then the join
KF_API double kf_lobby_find_id(const char *id)
{
    if (!g_init) return 0;
    uint64_t l = parse_u64(id);
    if (!l) return 0;
    g_find_id = l;
    code_of(l, g_find_code);
    g_find_pending = 0;
    g_found[0] = 0;
    if (S.MM_RequestData(g_mm, l)) g_find_pending++;
    if (!g_find_pending) { ev("notfound"); return 0; }
    return 1;
}

KF_API const char *kf_found_info(void) { return g_found; }

KF_API double kf_lobby_leave(void)
{
    if (!g_init || !g_lobby) return 0;
    S.MM_LeaveLobby(g_mm, g_lobby);
    g_lobby = 0;
    g_owner = 0;
    return 1;
}

KF_API const char *kf_lobby_id(void)
{
    snprintf(g_str, sizeof(g_str), "%llu", (unsigned long long)g_lobby);
    return g_str;
}

KF_API const char *kf_lobby_code(void)
{
    if (!g_lobby) return "";
    code_of(g_lobby, g_str);
    return g_str;
}

KF_API double kf_lobby_owner(void) { return (g_init && g_lobby) ? (double)acct_of(S.MM_GetLobbyOwner(g_mm, g_lobby)) : 0; }
KF_API double kf_lobby_count(void) { return (g_init && g_lobby) ? (double)S.MM_GetNumMembers(g_mm, g_lobby) : 0; }
KF_API double kf_lobby_member(double i) { return (g_init && g_lobby) ? (double)acct_of(S.MM_GetMember(g_mm, g_lobby, (int)i)) : 0; }

KF_API double kf_lobby_set(const char *k, const char *v)
{
    if (!g_init || !g_lobby || !k || !v) return 0;
    return S.MM_SetData(g_mm, g_lobby, k, v) ? 1 : 0;
}

KF_API const char *kf_lobby_get(const char *k)
{
    if (!g_init || !g_lobby || !k) return "";
    snprintf(g_str, sizeof(g_str), "%s", data_of(g_lobby, k));
    return g_str;
}

KF_API double kf_lobby_joinable(double on) { return (g_init && g_lobby) ? (S.MM_SetJoinable(g_mm, g_lobby, on != 0) ? 1 : 0) : 0; }
KF_API double kf_lobby_limit(double mx) { return (g_init && g_lobby) ? (S.MM_SetLimit(g_mm, g_lobby, (int)mx) ? 1 : 0) : 0; }

// BROWSE: the public Knight Fights lobbies -> "browse:<n>", then kf_browse_info(i) = "id|code|name|np|mx|ver|st"
KF_API double kf_browse(void)
{
    if (!g_init) return 0;
    S.MM_AddStringFilter(g_mm, "kfgame", "kfo", k_ELobbyComparisonEqual);
    S.MM_AddDistanceFilter(g_mm, k_ELobbyDistanceFilterWorldwide);
    S.MM_AddCountFilter(g_mm, 50);
    g_call_list = S.MM_RequestList(g_mm);
    return g_call_list != 0;
}

KF_API double kf_browse_count(void) { return g_browse_n; }

KF_API const char *kf_browse_info(double i)
{
    int k = (int)i;
    if (k < 0 || k >= g_browse_n) return "";
    return g_browse[k];
}

KF_API double kf_invite_overlay(void)
{
    if (!g_init || !g_lobby) return 0;
    S.Friends_InviteDialog(g_friends, g_lobby);
    return 1;
}

// ---------------------------------------------------------------- build 49: the in-game friends list and direct invites
// kf_friends_refresh() reads the Steam friends list (k_EFriendFlagImmediate) into a sorted copy: playing Knight Fights /
// Spacewar (app 480) first, then online, busy / away / snooze, then offline; each part by name. Returns how many (max 200),
// -1 when this steam_api64.dll has no friends-list functions. kf_friend_info(i): "acct|state|in480|name" ('|' in a name
// becomes '/'). kf_invite_user(acct): a Steam invite to the room we are in (the friend gets Steam's own notification, and
// a running Knight Fights shows its own invite box); 1 sent, 0 not.
#define KF_MAXF 200
static struct { uint32_t acct; int state; int in480; char name[96]; } g_fr[KF_MAXF];
static int g_fr_n = 0;

static int ci_cmp(const char *a, const char *b)
{
    for (;; a++, b++)
    {
        int x = (*a >= 'A' && *a <= 'Z') ? *a + 32 : (unsigned char)*a;
        int y = (*b >= 'A' && *b <= 'Z') ? *b + 32 : (unsigned char)*b;
        if (x != y || !x) return x - y;
    }
}

static int fr_rank(int i)
{
    if (g_fr[i].state != 0 && g_fr[i].in480) return 0;
    if (g_fr[i].state == 1) return 1;
    if (g_fr[i].state != 0) return 2;
    return 3;
}

KF_API double kf_friends_refresh(void)
{
    if (!g_init) return 0;
    if (!S.Friends_GetFriendCount || !S.Friends_GetFriendByIndex || !S.Friends_GetFriendPersonaState) return -1;
    int n = S.Friends_GetFriendCount(g_friends, 4 /* k_EFriendFlagImmediate */);
    g_fr_n = 0;
    for (int i = 0; i < n && g_fr_n < KF_MAXF; i++)
    {
        uint64_t sid = S.Friends_GetFriendByIndex(g_friends, i, 4);
        if (!sid) continue;
        int k = g_fr_n++;
        g_fr[k].acct = acct_of(sid);
        g_fr[k].state = S.Friends_GetFriendPersonaState(g_friends, sid);
        g_fr[k].in480 = 0;
        if (S.Friends_GetFriendGamePlayed)
        {
            FriendGameInfo_t gi;
            memset(&gi, 0, sizeof(gi));
            if (S.Friends_GetFriendGamePlayed(g_friends, sid, &gi) && (gi.m_gameID.ToUint64() & 0xFFFFFFULL) == 480) g_fr[k].in480 = 1;
        }
        const char *nm = S.Friends_GetFriendPersonaName(g_friends, sid);
        snprintf(g_fr[k].name, sizeof(g_fr[k].name), "%s", nm ? nm : "");
        for (char *p = g_fr[k].name; *p; p++)
            if (*p == '|') *p = '/';
    }
    // insertion sort: rank, then name (case-insensitive)
    for (int i = 1; i < g_fr_n; i++)
    {
        int j = i;
        while (j > 0)
        {
            int ra = fr_rank(j - 1), rb = fr_rank(j);
            int c = (ra != rb) ? (ra - rb) : ci_cmp(g_fr[j - 1].name, g_fr[j].name);
            if (c <= 0) break;
            auto t = g_fr[j]; g_fr[j] = g_fr[j - 1]; g_fr[j - 1] = t;
            j--;
        }
    }
    return g_fr_n;
}

KF_API const char *kf_friend_info(double i)
{
    int k = (int)i;
    if (k < 0 || k >= g_fr_n) return "";
    snprintf(g_str, sizeof(g_str), "%u|%d|%d|%s", g_fr[k].acct, g_fr[k].state, g_fr[k].in480, g_fr[k].name);
    return g_str;
}

KF_API double kf_invite_user(double acct)
{
    if (!g_init || !g_lobby || !S.MM_InviteUser || acct <= 0) return 0;
    return S.MM_InviteUser(g_mm, g_lobby, sid_of_acct(acct)) ? 1 : 0;
}

KF_API double kf_overlay_on(void) { return (g_init && S.Utils_Overlay(g_utils)) ? 1 : 0; }

KF_API const char *kf_launch_lobby(void) { return g_launch; }

// ---------------------------------------------------------------- packets
// one message (a line of JSON text) to a player; reliable = in order and re-sent until it arrives; else it may be dropped
// (SOUL positions, pings). Unreliable packets are limited to 1200 bytes by Steam: longer ones go reliable.
KF_API double kf_send(double acct, const char *text, double reliable)
{
    if (!g_init || !text) return 0;
    size_t n = strlen(text);
    if (n == 0 || n > 65536) return 0;
    int mode = (reliable != 0 || n > 1200) ? 2 /* k_EP2PSendReliable */ : 0 /* k_EP2PSendUnreliable */;
    return S.NET_Send(g_net, sid_of_acct(acct), text, (uint32_t)n, mode, 0) ? 1 : 0;
}

// the next packet's text ("" when there is none); kf_recv_from() = its sender's account
KF_API const char *kf_recv(void)
{
    if (!g_init) return "";
    for (int tries = 0; tries < 8; tries++)
    {
        uint32_t sz = 0;
        if (!S.NET_Avail(g_net, &sz, 0)) return "";
        uint32_t got = 0;
        uint64_t from = 0;
        if (sz > 65536)
        {
            // too big for us: read and drop
            static char junk[1024];
            S.NET_Read(g_net, junk, sizeof(junk), &got, &from, 0);
            continue;
        }
        if (!S.NET_Read(g_net, g_recv, 65536, &got, &from, 0)) return "";
        g_recv[got] = 0;
        if (strlen(g_recv) != got) continue;  // a NUL inside: not one of ours
        g_last_from = from;
        return g_recv;
    }
    return "";
}

KF_API double kf_recv_from(void) { return (double)acct_of(g_last_from); }

// ---------------------------------------------------------------- the callback pump
static void on_list(SteamAPICall_t call, LobbyMatchList_t *r)
{
    if (call == g_call_list)
    {
        g_call_list = 0;
        g_browse_n = 0;
        for (uint32 i = 0; i < r->m_nLobbiesMatching && g_browse_n < 50; i++)
        {
            uint64_t id = S.MM_GetLobbyByIndex(g_mm, (int)i);
            if (!id) continue;
            lobby_line(id, g_browse[g_browse_n], sizeof(g_browse[0]), 1);
            g_browse_n++;
        }
        char b[32];
        snprintf(b, sizeof(b), "browse:%d", g_browse_n);
        ev(b);
    }
    else if (call == g_call_find_list)
    {
        g_call_find_list = 0;
        if (g_find_pending > 0) g_find_pending--;
        if (g_found[0]) return;
        for (uint32 i = 0; i < r->m_nLobbiesMatching; i++)
        {
            uint64_t id = S.MM_GetLobbyByIndex(g_mm, (int)i);
            if (id && strcmp(data_of(id, "kfgame"), "kfo") == 0 && strcmp(data_of(id, "kfcode"), g_find_code) == 0)
            {
                char line[400];
                lobby_line(id, line, sizeof(line), 0);
                snprintf(g_found, sizeof(g_found), "%s", line);
                char e[460];
                snprintf(e, sizeof(e), "found:%s", line);
                ev(e);
                return;
            }
        }
        if (g_find_pending == 0) ev("notfound");
    }
}

static void pump(void)
{
    S.MD_RunFrame(g_pipe);
    CallbackMsg_t msg;
    char e[256];
    while (S.MD_GetNext(g_pipe, &msg))
    {
        switch (msg.m_iCallback)
        {
        case SteamAPICallCompleted_t::k_iCallback:
        {
            SteamAPICallCompleted_t *c = (SteamAPICallCompleted_t *)msg.m_pubParam;
            bool failed = false;
            if (c->m_hAsyncCall == g_call_create && g_call_create)
            {
                LobbyCreated_t r;
                memset(&r, 0, sizeof(r));
                g_call_create = 0;
                if (S.MD_Result(g_pipe, c->m_hAsyncCall, &r, sizeof(r), LobbyCreated_t::k_iCallback, &failed) && !failed && r.m_eResult == k_EResultOK)
                {
                    // LobbyEnter_t follows (the creator is in it): the room's tags go on now
                    char code[8];
                    code_of(r.m_ulSteamIDLobby, code);
                    S.MM_SetData(g_mm, r.m_ulSteamIDLobby, "kfgame", "kfo");
                    S.MM_SetData(g_mm, r.m_ulSteamIDLobby, "kfcode", code);
                }
                else
                {
                    snprintf(e, sizeof(e), "create_failed:%d", (int)r.m_eResult);
                    ev(e);
                }
            }
            else if (c->m_hAsyncCall == g_call_join && g_call_join)
            {
                LobbyEnter_t r;
                memset(&r, 0, sizeof(r));
                g_call_join = 0;
                if (!(S.MD_Result(g_pipe, c->m_hAsyncCall, &r, sizeof(r), LobbyEnter_t::k_iCallback, &failed) && !failed &&
                      r.m_EChatRoomEnterResponse == k_EChatRoomEnterResponseSuccess))
                {
                    snprintf(e, sizeof(e), "join_failed:%d", (int)r.m_EChatRoomEnterResponse);
                    ev(e);
                }
                // success: LobbyEnter_t comes as a callback too (handled below)
            }
            else if ((c->m_hAsyncCall == g_call_list && g_call_list) || (c->m_hAsyncCall == g_call_find_list && g_call_find_list))
            {
                LobbyMatchList_t r;
                memset(&r, 0, sizeof(r));
                if (S.MD_Result(g_pipe, c->m_hAsyncCall, &r, sizeof(r), LobbyMatchList_t::k_iCallback, &failed) && !failed)
                    on_list(c->m_hAsyncCall, &r);
                else
                {
                    LobbyMatchList_t z;
                    memset(&z, 0, sizeof(z));
                    on_list(c->m_hAsyncCall, &z);
                }
            }
            break;
        }
        case LobbyEnter_t::k_iCallback:
        {
            LobbyEnter_t *r = (LobbyEnter_t *)msg.m_pubParam;
            if (r->m_EChatRoomEnterResponse == k_EChatRoomEnterResponseSuccess)
            {
                g_lobby = r->m_ulSteamIDLobby;
                g_owner = S.MM_GetLobbyOwner(g_mm, g_lobby);
                ev("joined");
            }
            break;
        }
        case LobbyChatUpdate_t::k_iCallback:
        {
            LobbyChatUpdate_t *r = (LobbyChatUpdate_t *)msg.m_pubParam;
            if (r->m_ulSteamIDLobby != g_lobby || !g_lobby) break;
            if (r->m_rgfChatMemberStateChange & k_EChatMemberStateChangeEntered)
                snprintf(e, sizeof(e), "member_in:%u", acct_of(r->m_ulSteamIDUserChanged));
            else
            {
                snprintf(e, sizeof(e), "member_out:%u", acct_of(r->m_ulSteamIDUserChanged));
                S.NET_Close(g_net, r->m_ulSteamIDUserChanged);
            }
            ev(e);
            break;
        }
        case LobbyDataUpdate_t::k_iCallback:
        {
            LobbyDataUpdate_t *r = (LobbyDataUpdate_t *)msg.m_pubParam;
            // a code / invite lookup waits for exactly this lobby's data
            if (r->m_ulSteamIDLobby == g_find_id && r->m_ulSteamIDMember == r->m_ulSteamIDLobby && g_find_pending > 0)
            {
                g_find_pending--;
                if (!g_found[0] && r->m_bSuccess && strcmp(data_of(g_find_id, "kfgame"), "kfo") == 0 &&
                    strcmp(data_of(g_find_id, "kfcode"), g_find_code) == 0)
                {
                    char line[400];
                    lobby_line(g_find_id, line, sizeof(line), 0);
                    snprintf(g_found, sizeof(g_found), "%s", line);
                    char e2[460];
                    snprintf(e2, sizeof(e2), "found:%s", line);
                    ev(e2);
                }
                else if (!g_found[0] && g_find_pending == 0)
                    ev("notfound");
            }
            break;
        }
        case LobbyKicked_t::k_iCallback:
        {
            LobbyKicked_t *r = (LobbyKicked_t *)msg.m_pubParam;
            if (r->m_ulSteamIDLobby == g_lobby)
            {
                g_lobby = 0;
                ev("left");
            }
            break;
        }
        case LobbyInvite_t::k_iCallback:
        {
            // build 49: a friend invited us to their room while this game runs: "invited:<lobby>|<acct>"
            LobbyInvite_t *r = (LobbyInvite_t *)msg.m_pubParam;
            snprintf(e, sizeof(e), "invited:%llu|%u", (unsigned long long)r->m_ulSteamIDLobby, acct_of(r->m_ulSteamIDUser));
            ev(e);
            break;
        }
        case GameLobbyJoinRequested_t::k_iCallback:
        {
            GameLobbyJoinRequested_t *r = (GameLobbyJoinRequested_t *)msg.m_pubParam;
            snprintf(e, sizeof(e), "join_request:%llu", (unsigned long long)r->m_steamIDLobby.ConvertToUint64());
            ev(e);
            break;
        }
        case P2PSessionRequest_t::k_iCallback:
        {
            P2PSessionRequest_t *r = (P2PSessionRequest_t *)msg.m_pubParam;
            uint64_t who = r->m_steamIDRemote.ConvertToUint64();
            // only the players of our room may open a connection to us
            if (is_member(who)) S.NET_Accept(g_net, who);
            break;
        }
        case P2PSessionConnectFail_t::k_iCallback:
        {
            P2PSessionConnectFail_t *r = (P2PSessionConnectFail_t *)msg.m_pubParam;
            snprintf(e, sizeof(e), "p2p_fail:%u", acct_of(r->m_steamIDRemote.ConvertToUint64()));
            ev(e);
            break;
        }
        default:
            break;
        }
        S.MD_Free(g_pipe);
    }
    // the owner changed (the old host left): every game hears it the same way
    if (g_lobby)
    {
        uint64_t o = S.MM_GetLobbyOwner(g_mm, g_lobby);
        if (o && o != g_owner)
        {
            g_owner = o;
            snprintf(e, sizeof(e), "owner:%u", acct_of(o));
            ev(e);
        }
    }
}

// the next event ("" when there is none); GameMaker calls it until it gets ""
KF_API const char *kf_poll(void)
{
    if (!g_init) return "";
    if (g_ev_head == g_ev_tail) pump();
    if (g_ev_head == g_ev_tail) return "";
    snprintf(g_str, sizeof(g_str), "%s", g_evq[g_ev_head]);
    g_ev_head = (g_ev_head + 1) % EVQ;
    return g_str;
}

#ifdef _WIN32
BOOL APIENTRY DllMain(HMODULE, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_DETACH && g_init && g_lobby) S.MM_LeaveLobby(g_mm, g_lobby);
    return TRUE;
}
#endif
