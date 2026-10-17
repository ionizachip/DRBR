// mock_steam_api.cpp - a stand-in libsteam_api.so for testing kf_steam on Linux (build 45 tests only; never shipped).
// Every flat API call kf_steam uses becomes one request to a Python "Steam" (mock_steam_backend.py) over a UNIX socket
// (KF_MOCK_SOCK); one process = one Steam user (KF_MOCK_ACCT, KF_MOCK_NAME). Callbacks and call results come back as text
// and are turned into the real SDK structs, so kf_steam's dispatch code runs exactly as it would against Steam.
// This tests kf_steam's own logic (codes, lookups, members, owners, packets, dispatch). It is NOT a test of Steam.

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <string>
#include <vector>
#include "steam/steam_api.h"

#define MOCK_API extern "C" __attribute__((visibility("default")))

static int g_fd = -1;
static std::string g_rbuf;

static bool mconnect()
{
    if (g_fd >= 0) return true;
    const char *p = getenv("KF_MOCK_SOCK");
    if (!p) return false;
    g_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    sockaddr_un a;
    memset(&a, 0, sizeof(a));
    a.sun_family = AF_UNIX;
    strncpy(a.sun_path, p, sizeof(a.sun_path) - 1);
    if (connect(g_fd, (sockaddr *)&a, sizeof(a)) != 0) { close(g_fd); g_fd = -1; return false; }
    return true;
}

static std::string line()
{
    for (;;)
    {
        size_t n = g_rbuf.find('\n');
        if (n != std::string::npos)
        {
            std::string l = g_rbuf.substr(0, n);
            g_rbuf.erase(0, n + 1);
            return l;
        }
        char b[4096];
        ssize_t r = read(g_fd, b, sizeof(b));
        if (r <= 0) return "";
        g_rbuf.append(b, (size_t)r);
    }
}

static std::string rpc(const std::string &req)
{
    if (!mconnect()) return "";
    std::string s = req + "\n";
    ssize_t off = 0;
    while (off < (ssize_t)s.size())
    {
        ssize_t w = write(g_fd, s.data() + off, s.size() - off);
        if (w <= 0) return "";
        off += w;
    }
    return line();
}

static std::vector<std::string> split(const std::string &s)
{
    std::vector<std::string> v;
    size_t a = 0;
    for (;;)
    {
        size_t b = s.find('\t', a);
        v.push_back(s.substr(a, b == std::string::npos ? std::string::npos : b - a));
        if (b == std::string::npos) break;
        a = b + 1;
    }
    return v;
}

static uint64_t u64(const std::string &s) { return strtoull(s.c_str(), NULL, 10); }
static std::string S(uint64_t v) { char b[32]; snprintf(b, sizeof(b), "%llu", (unsigned long long)v); return b; }
static std::string I(long long v) { char b[32]; snprintf(b, sizeof(b), "%lld", v); return b; }

// ---------------------------------------------------------------- init / pipe
static char g_name[128] = "";
static uint64_t g_me = 0;
static int g_dummy_iface = 1;

MOCK_API ESteamAPIInitResult SteamAPI_InitFlat(SteamErrMsg *err)
{
    const char *acct = getenv("KF_MOCK_ACCT");
    const char *nm = getenv("KF_MOCK_NAME");
    const char *off = getenv("KF_MOCK_OFFLINE");
    if (off && off[0] == '1')
    {
        if (err) snprintf(*err, sizeof(SteamErrMsg), "No Steam client (mock)");
        return k_ESteamAPIInitResult_NoSteamClient;
    }
    if (!acct || !mconnect())
    {
        if (err) snprintf(*err, sizeof(SteamErrMsg), "mock backend not reachable");
        return k_ESteamAPIInitResult_NoSteamClient;
    }
    const char *app = getenv("SteamAppId");
    std::string r = rpc(std::string("hello\t") + acct + "\t" + (nm ? nm : "Player") + "\t" + (app ? app : "0"));
    g_me = 76561197960265728ULL + strtoull(acct, NULL, 10);
    snprintf(g_name, sizeof(g_name), "%s", nm ? nm : "Player");
    return r == "ok" ? k_ESteamAPIInitResult_OK : k_ESteamAPIInitResult_FailedGeneric;
}
MOCK_API void SteamAPI_Shutdown() { rpc("bye"); }
MOCK_API HSteamPipe SteamAPI_GetHSteamPipe() { return 1; }
MOCK_API void SteamAPI_ManualDispatch_Init() {}

// ---------------------------------------------------------------- callbacks
static std::vector<std::string> g_cbs;
static unsigned char g_cbbuf[1024];
static CallbackMsg_t g_cur;

MOCK_API void SteamAPI_ManualDispatch_RunFrame(HSteamPipe)
{
    std::string r = rpc("frame");
    int n = atoi(r.c_str());
    for (int i = 0; i < n; i++) g_cbs.push_back(line());
}

static int fill(int id, const std::vector<std::string> &f, void *out, int cap)
{
    memset(out, 0, cap);
    switch (id)
    {
    case SteamAPICallCompleted_t::k_iCallback: { SteamAPICallCompleted_t *c = (SteamAPICallCompleted_t *)out; c->m_hAsyncCall = u64(f[1]); c->m_iCallback = atoi(f[2].c_str()); c->m_cubParam = atoi(f[3].c_str()); return sizeof(*c); }
    case LobbyEnter_t::k_iCallback: { LobbyEnter_t *c = (LobbyEnter_t *)out; c->m_ulSteamIDLobby = u64(f[1]); c->m_rgfChatPermissions = 0; c->m_bLocked = false; c->m_EChatRoomEnterResponse = (uint32)atoi(f[2].c_str()); return sizeof(*c); }
    case LobbyDataUpdate_t::k_iCallback: { LobbyDataUpdate_t *c = (LobbyDataUpdate_t *)out; c->m_ulSteamIDLobby = u64(f[1]); c->m_ulSteamIDMember = u64(f[2]); c->m_bSuccess = atoi(f[3].c_str()); return sizeof(*c); }
    case LobbyChatUpdate_t::k_iCallback: { LobbyChatUpdate_t *c = (LobbyChatUpdate_t *)out; c->m_ulSteamIDLobby = u64(f[1]); c->m_ulSteamIDUserChanged = u64(f[2]); c->m_ulSteamIDMakingChange = u64(f[2]); c->m_rgfChatMemberStateChange = (uint32)atoi(f[3].c_str()); return sizeof(*c); }
    case LobbyCreated_t::k_iCallback: { LobbyCreated_t *c = (LobbyCreated_t *)out; c->m_eResult = (EResult)atoi(f[1].c_str()); c->m_ulSteamIDLobby = u64(f[2]); return sizeof(*c); }
    case LobbyMatchList_t::k_iCallback: { LobbyMatchList_t *c = (LobbyMatchList_t *)out; c->m_nLobbiesMatching = (uint32)atoi(f[1].c_str()); return sizeof(*c); }
    case LobbyKicked_t::k_iCallback: { LobbyKicked_t *c = (LobbyKicked_t *)out; c->m_ulSteamIDLobby = u64(f[1]); c->m_ulSteamIDAdmin = u64(f[2]); c->m_bKickedDueToDisconnect = atoi(f[3].c_str()); return sizeof(*c); }
    case LobbyInvite_t::k_iCallback: { LobbyInvite_t *c = (LobbyInvite_t *)out; c->m_ulSteamIDUser = u64(f[1]); c->m_ulSteamIDLobby = u64(f[2]); c->m_ulGameID = 480; return sizeof(*c); }
    case GameLobbyJoinRequested_t::k_iCallback: { GameLobbyJoinRequested_t *c = (GameLobbyJoinRequested_t *)out; c->m_steamIDLobby.SetFromUint64(u64(f[1])); c->m_steamIDFriend.SetFromUint64(u64(f[2])); return sizeof(*c); }
    case P2PSessionRequest_t::k_iCallback: { P2PSessionRequest_t *c = (P2PSessionRequest_t *)out; c->m_steamIDRemote.SetFromUint64(u64(f[1])); return sizeof(*c); }
    case P2PSessionConnectFail_t::k_iCallback: { P2PSessionConnectFail_t *c = (P2PSessionConnectFail_t *)out; c->m_steamIDRemote.SetFromUint64(u64(f[1])); c->m_eP2PSessionError = (uint8)atoi(f[2].c_str()); return sizeof(*c); }
    }
    return 0;
}

MOCK_API bool SteamAPI_ManualDispatch_GetNextCallback(HSteamPipe, CallbackMsg_t *m)
{
    if (g_cbs.empty()) return false;
    std::vector<std::string> f = split(g_cbs.front());
    g_cbs.erase(g_cbs.begin());
    int id = atoi(f[0].c_str());
    int sz = fill(id, f, g_cbbuf, sizeof(g_cbbuf));
    m->m_hSteamUser = 1;
    m->m_iCallback = id;
    m->m_pubParam = g_cbbuf;
    m->m_cubParam = sz;
    g_cur = *m;
    return true;
}
MOCK_API void SteamAPI_ManualDispatch_FreeLastCallback(HSteamPipe) {}

MOCK_API bool SteamAPI_ManualDispatch_GetAPICallResult(HSteamPipe, SteamAPICall_t call, void *out, int cap, int expected, bool *failed)
{
    std::string r = rpc("result\t" + S(call));
    if (r.empty() || r == "none") { if (failed) *failed = true; return false; }
    std::vector<std::string> f = split(r);
    if (atoi(f[0].c_str()) != expected) { if (failed) *failed = true; return false; }
    fill(expected, f, out, cap);
    if (failed) *failed = false;
    return true;
}

// ---------------------------------------------------------------- interfaces (any non-null pointer)
MOCK_API void *SteamAPI_SteamUser_v023() { return &g_dummy_iface; }
MOCK_API void *SteamAPI_SteamFriends_v018() { return &g_dummy_iface; }
MOCK_API void *SteamAPI_SteamUtils_v011() { return &g_dummy_iface; }
MOCK_API void *SteamAPI_SteamMatchmaking_v009() { return &g_dummy_iface; }
MOCK_API void *SteamAPI_SteamNetworking_v006() { return &g_dummy_iface; }

MOCK_API uint64_t SteamAPI_ISteamUser_GetSteamID(void *) { return g_me; }
MOCK_API const char *SteamAPI_ISteamFriends_GetPersonaName(void *) { return g_name; }
static char g_nbuf[256];
MOCK_API const char *SteamAPI_ISteamFriends_GetFriendPersonaName(void *, uint64_t id) { snprintf(g_nbuf, sizeof(g_nbuf), "%s", rpc("name\t" + S(id)).c_str()); return g_nbuf; }
MOCK_API void SteamAPI_ISteamFriends_ActivateGameOverlayInviteDialog(void *, uint64_t lobby) { rpc("invite_dialog\t" + S(lobby)); }
MOCK_API bool SteamAPI_ISteamUtils_IsOverlayEnabled(void *) { return rpc("overlay") == "1"; }
// build 49: the friends list (every other connected user; "fstate" decides offline / away) and direct invites
MOCK_API int SteamAPI_ISteamFriends_GetFriendCount(void *, int) { return atoi(rpc("fcount").c_str()); }
MOCK_API uint64_t SteamAPI_ISteamFriends_GetFriendByIndex(void *, int i, int) { return u64(rpc("fget\t" + I(i))); }
MOCK_API int SteamAPI_ISteamFriends_GetFriendPersonaState(void *, uint64_t id) { return atoi(rpc("fstate\t" + S(id)).c_str()); }
MOCK_API bool SteamAPI_ISteamFriends_GetFriendGamePlayed(void *, uint64_t id, FriendGameInfo_t *g) { std::string r = rpc("fgame\t" + S(id)); if (r == "0" || r.empty()) return false; g->m_gameID = CGameID((uint64)atoll(r.c_str())); return true; }
MOCK_API bool SteamAPI_ISteamMatchmaking_InviteUserToLobby(void *, uint64_t l, uint64_t who) { return rpc("invite\t" + S(l) + "\t" + S(who)) == "1"; }

// ---------------------------------------------------------------- matchmaking
MOCK_API SteamAPICall_t SteamAPI_ISteamMatchmaking_CreateLobby(void *, int type, int max) { return u64(rpc("create\t" + I(type) + "\t" + I(max))); }
MOCK_API SteamAPICall_t SteamAPI_ISteamMatchmaking_JoinLobby(void *, uint64_t l) { return u64(rpc("join\t" + S(l))); }
MOCK_API void SteamAPI_ISteamMatchmaking_LeaveLobby(void *, uint64_t l) { rpc("leave\t" + S(l)); }
MOCK_API uint64_t SteamAPI_ISteamMatchmaking_GetLobbyOwner(void *, uint64_t l) { return u64(rpc("owner\t" + S(l))); }
MOCK_API int SteamAPI_ISteamMatchmaking_GetNumLobbyMembers(void *, uint64_t l) { return atoi(rpc("count\t" + S(l)).c_str()); }
MOCK_API uint64_t SteamAPI_ISteamMatchmaking_GetLobbyMemberByIndex(void *, uint64_t l, int i) { return u64(rpc("member\t" + S(l) + "\t" + I(i))); }
MOCK_API bool SteamAPI_ISteamMatchmaking_SetLobbyData(void *, uint64_t l, const char *k, const char *v) { return rpc("setdata\t" + S(l) + "\t" + k + "\t" + v) == "1"; }
static char g_dbuf[8192];
MOCK_API const char *SteamAPI_ISteamMatchmaking_GetLobbyData(void *, uint64_t l, const char *k) { snprintf(g_dbuf, sizeof(g_dbuf), "%s", rpc("getdata\t" + S(l) + "\t" + k).c_str()); return g_dbuf; }
MOCK_API bool SteamAPI_ISteamMatchmaking_SetLobbyJoinable(void *, uint64_t l, bool on) { return rpc("joinable\t" + S(l) + "\t" + I(on)) == "1"; }
MOCK_API bool SteamAPI_ISteamMatchmaking_SetLobbyMemberLimit(void *, uint64_t l, int m) { return rpc("limit\t" + S(l) + "\t" + I(m)) == "1"; }
MOCK_API bool SteamAPI_ISteamMatchmaking_RequestLobbyData(void *, uint64_t l) { return rpc("reqdata\t" + S(l)) == "1"; }
MOCK_API void SteamAPI_ISteamMatchmaking_AddRequestLobbyListStringFilter(void *, const char *k, const char *v, int cmp) { rpc(std::string("filter\t") + k + "\t" + v + "\t" + I(cmp)); }
MOCK_API void SteamAPI_ISteamMatchmaking_AddRequestLobbyListDistanceFilter(void *, int) {}
MOCK_API void SteamAPI_ISteamMatchmaking_AddRequestLobbyListResultCountFilter(void *, int n) { rpc("countfilter\t" + I(n)); }
MOCK_API SteamAPICall_t SteamAPI_ISteamMatchmaking_RequestLobbyList(void *) { return u64(rpc("list")); }
MOCK_API uint64_t SteamAPI_ISteamMatchmaking_GetLobbyByIndex(void *, int i) { return u64(rpc("listget\t" + I(i))); }

// ---------------------------------------------------------------- networking (payloads as hex)
static std::string hex(const void *d, uint32_t n)
{
    static const char *H = "0123456789abcdef";
    std::string s;
    s.reserve(n * 2);
    const unsigned char *p = (const unsigned char *)d;
    for (uint32_t i = 0; i < n; i++) { s += H[p[i] >> 4]; s += H[p[i] & 15]; }
    return s;
}
MOCK_API bool SteamAPI_ISteamNetworking_SendP2PPacket(void *, uint64_t to, const void *d, uint32_t n, int type, int ch)
{
    return rpc("send\t" + S(to) + "\t" + I(type) + "\t" + I(ch) + "\t" + hex(d, n)) == "1";
}
static std::string g_pkt;
static uint64_t g_pkt_from = 0;
MOCK_API bool SteamAPI_ISteamNetworking_IsP2PPacketAvailable(void *, uint32_t *sz, int ch)
{
    std::string r = rpc("avail\t" + I(ch));
    if (r.empty() || r == "-1") return false;
    *sz = (uint32_t)atoi(r.c_str());
    return true;
}
MOCK_API bool SteamAPI_ISteamNetworking_ReadP2PPacket(void *, void *out, uint32_t cap, uint32_t *got, uint64_t *from, int ch)
{
    std::string r = rpc("read\t" + I(ch));
    if (r.empty() || r == "none") return false;
    std::vector<std::string> f = split(r);
    *from = u64(f[0]);
    const std::string &h = f[1];
    uint32_t n = (uint32_t)(h.size() / 2);
    unsigned char *o = (unsigned char *)out;
    uint32_t w = 0;
    for (uint32_t i = 0; i < n && w < cap; i++)
    {
        auto v = [](char c) { return (c >= 'a') ? (c - 'a' + 10) : (c - '0'); };
        o[w++] = (unsigned char)((v(h[2 * i]) << 4) | v(h[2 * i + 1]));
    }
    *got = w;
    return true;
}
MOCK_API bool SteamAPI_ISteamNetworking_AcceptP2PSessionWithUser(void *, uint64_t who) { return rpc("accept\t" + S(who)) == "1"; }
MOCK_API bool SteamAPI_ISteamNetworking_CloseP2PSessionWithUser(void *, uint64_t who) { return rpc("closep2p\t" + S(who)) == "1"; }
MOCK_API bool SteamAPI_ISteamNetworking_AllowP2PPacketRelay(void *, bool) { return true; }
