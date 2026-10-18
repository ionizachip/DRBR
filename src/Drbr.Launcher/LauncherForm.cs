// DRBR Launcher's window.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace Drbr
{
    sealed class LauncherForm : Form
    {
        static readonly Color Bg = Color.Black, Fg = Color.White, Accent = Color.FromArgb(255, 213, 0), Dim = Color.FromArgb(150, 150, 150), Panel = Color.FromArgb(24, 24, 32);
        readonly DrbrPaths P;
        readonly LauncherCore C;
        readonly Dictionary<string, string> A;
        readonly Label lblInstalled = new Label(), lblSave = new Label(), lblUpdate = new Label(), lblStatus = new Label();
        readonly Button btnPlay = new Button(), btnCheck = new Button(), btnUpdate = new Button(), btnRepair = new Button(), btnRestore = new Button(),
                        btnSettings = new Button(), btnNotes = new Button(), btnFolder = new Button();
        readonly ProgressBar bar = new ProgressBar();
        UpdateInfo latest;
        bool busy;

        public LauncherForm(DrbrPaths p, Dictionary<string, string> a)
        {
            P = p;
            A = a;
            C = new LauncherCore(p);
            AutoScaleDimensions = new SizeF(96F, 96F);
            AutoScaleMode = AutoScaleMode.Dpi;
            Text = "DRBR Launcher";
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(560, 470);
            BackColor = Bg;
            ForeColor = Fg;
            Font = new Font("Segoe UI", 10f);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

            Label t1 = new Label { Text = "DRBR", Font = new Font("Segoe UI", 34f, FontStyle.Bold), ForeColor = Fg, AutoSize = false, TextAlign = ContentAlignment.MiddleCenter, Bounds = new Rectangle(0, 14, 560, 60) };
            Label t2 = new Label { Text = "DELTARUNE BATTLE ROYALE", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Accent, AutoSize = false, TextAlign = ContentAlignment.MiddleCenter, Bounds = new Rectangle(0, 74, 560, 24) };
            Controls.Add(t1);
            Controls.Add(t2);

            Panel info = new Panel { Bounds = new Rectangle(30, 112, 500, 92), BackColor = Panel };
            foreach (Label l in new[] { lblInstalled, lblSave, lblUpdate }) { l.AutoSize = false; l.ForeColor = Fg; info.Controls.Add(l); }
            lblInstalled.Bounds = new Rectangle(14, 8, 480, 24);
            lblSave.Bounds = new Rectangle(14, 34, 480, 24);
            lblUpdate.Bounds = new Rectangle(14, 60, 480, 24);
            Controls.Add(info);

            Big(btnPlay, "PLAY DRBR", new Rectangle(130, 218, 300, 56));
            btnPlay.Click += (s, e) => Play();

            int y = 290;
            Small(btnCheck, "Check for Updates", new Rectangle(30, y, 160, 34)); btnCheck.Click += (s, e) => CheckUpdates(true);
            Small(btnUpdate, "Install Update", new Rectangle(200, y, 160, 34)); btnUpdate.Click += (s, e) => InstallUpdate(); btnUpdate.Enabled = false;
            Small(btnRepair, "Repair Installation", new Rectangle(370, y, 160, 34)); btnRepair.Click += (s, e) => Repair();
            y += 42;
            Small(btnRestore, "Restore Starting Save", new Rectangle(30, y, 160, 34)); btnRestore.Click += (s, e) => RestoreSave();
            Small(btnSettings, "Settings", new Rectangle(200, y, 160, 34)); btnSettings.Click += (s, e) => OpenSettings();
            Small(btnNotes, "Release Notes", new Rectangle(370, y, 160, 34)); btnNotes.Click += (s, e) => ShowNotes();
            y += 42;
            Small(btnFolder, "Open Installation Folder", new Rectangle(160, y, 240, 34)); btnFolder.Click += (s, e) => { try { Process.Start("explorer.exe", "\"" + P.Root + "\""); } catch { } };

            bar.Bounds = new Rectangle(30, 418, 500, 12);
            bar.Visible = false;
            Controls.Add(bar);
            lblStatus.Bounds = new Rectangle(30, 434, 500, 30);
            lblStatus.ForeColor = Dim;
            lblStatus.Font = new Font("Segoe UI", 8.5f);
            Controls.Add(lblStatus);
            Log.Line += (lvl, text) => { if (lvl != "INFO" || busy) Ui(() => lblStatus.Text = text); };
            Shown += (s, e) => Startup();
        }

        void Big(Button b, string text, Rectangle r)
        {
            b.Text = text; b.Bounds = r; b.FlatStyle = FlatStyle.Flat; b.BackColor = Accent; b.ForeColor = Color.Black;
            b.Font = new Font("Segoe UI", 16f, FontStyle.Bold); b.FlatAppearance.BorderSize = 0;
            Controls.Add(b);
        }

        void Small(Button b, string text, Rectangle r)
        {
            b.Text = text; b.Bounds = r; b.FlatStyle = FlatStyle.Flat; b.BackColor = Panel; b.ForeColor = Fg;
            b.FlatAppearance.BorderColor = Color.FromArgb(70, 70, 90);
            Controls.Add(b);
        }

        void Ui(Action a)
        {
            if (IsDisposed) return;
            try { if (InvokeRequired) BeginInvoke(a); else a(); } catch { }
        }

        void Busy(bool on, string text = null)
        {
            Ui(() =>
            {
                busy = on;
                foreach (Button b in new[] { btnPlay, btnCheck, btnRepair, btnRestore, btnSettings }) b.Enabled = !on;
                btnUpdate.Enabled = !on && latest != null && latest.Available;
                bar.Visible = on;
                if (text != null) lblStatus.Text = text;
            });
        }

        void Progress(string text, int pct)
        {
            Ui(() => { bar.Value = Math.Max(0, Math.Min(100, pct)); lblStatus.Text = text; });
        }

        void Background(Action work)
        {
            Thread t = new Thread(() =>
            {
                try { work(); }
                catch (DrbrException e) { Ui(() => MessageBox.Show(this, e.Message, "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Warning)); Log.Error(e.Message); }
                catch (Exception e) { Ui(() => MessageBox.Show(this, e.Message, "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Error)); Log.Error(e.ToString()); }
                finally { Busy(false); Ui(Refresh2); }
            });
            t.IsBackground = true;
            t.Start();
        }

        void Refresh2()
        {
            string v = C.Engine.InstalledVersion();
            Manifest m = null;
            try { m = C.InstalledManifest(); } catch { }
            lblInstalled.Text = v != null ? "Installed: DRBR " + v + (m != null ? "  (game build " + m.ModBuild + ")" : "") : "DRBR is not installed - run DRBR-Setup.exe";
            lblSave.Text = "Starting save: Pre-Roaring Knight room" + (C.Settings.StartMode == SaveProfile.ModeContinue ? "  (continue mode)" : "");
            if (latest == null) lblUpdate.Text = BuildInfo.UpdatesConfigured || UpdateEngine.DefaultUrl(C.Settings) != null ? "Updates: not checked yet" : "Updates: not set up in this build";
            else lblUpdate.Text = latest.Available ? "UPDATE AVAILABLE: " + latest.Manifest.Version + " (installed " + (latest.Installed ?? "-") + ")" : "Up to date (" + latest.Manifest.Version + ")";
            lblUpdate.ForeColor = latest != null && latest.Available ? Accent : Fg;
            btnPlay.Enabled = v != null && !busy;
            btnUpdate.Enabled = !busy && latest != null && latest.Available;
        }

        void Startup()
        {
            Refresh2();
            if (A.ContainsKey("updated")) lblStatus.Text = "DRBR Launcher was updated to " + BuildInfo.Version + ".";
            if (A.ContainsKey("update-failed")) lblStatus.Text = "The launcher could not update itself; this version keeps working.";
            if (A.ContainsKey("uninstall")) { BeginInvoke((Action)Uninstall); return; }
            if (A.ContainsKey("autoplay")) { BeginInvoke((Action)Play); return; }
            string rec = C.Engine.RecoverInterrupted();
            if (rec != null) lblStatus.Text = rec;
            Dictionary<string, string> pj = C.PendingJoin();
            if (pj.Count > 0)
            {
                lblStatus.Text = "You tried to join a room whose players have a newer DRBR. Checking for the update...";
                CheckUpdates(false, true);
                return;
            }
            if (C.Settings.CheckUpdatesOnStart && UpdateEngine.DefaultUrl(C.Settings) != null) CheckUpdates(false);
        }

        void CheckUpdates(bool loud, bool forJoin = false)
        {
            Busy(true, "Checking for updates...");
            Background(() =>
            {
                try { latest = C.Check(); }
                catch (DrbrException e) when (!loud && (e.Code == "offline" || e.Code == "updates_off")) { Log.Warn(e.Message); Ui(() => lblStatus.Text = e.Message); return; }
                Ui(() =>
                {
                    Refresh2();
                    if (latest.Available) AskUpdate(forJoin);
                    else if (loud) MessageBox.Show(this, "DRBR is up to date (" + latest.Manifest.Version + ").", "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information);
                });
            });
        }

        void AskUpdate(bool forJoin)
        {
            using (Form f = new Form { Text = "DRBR UPDATE AVAILABLE", ClientSize = new Size(440, 210), FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, BackColor = Bg, ForeColor = Fg, MaximizeBox = false, MinimizeBox = false, Font = Font })
            {
                f.Controls.Add(new Label { Text = "DRBR UPDATE AVAILABLE", Font = new Font("Segoe UI", 13f, FontStyle.Bold), ForeColor = Accent, Bounds = new Rectangle(20, 14, 380, 28) });
                string body = "Installed: " + (latest.Installed ?? "-") + "\nAvailable: " + latest.Manifest.Version;
                if (latest.ProtocolChanged || forJoin) body += "\n\nOnline play needs this update (players on the new version cannot play with older ones).";
                f.Controls.Add(new Label { Text = body, Bounds = new Rectangle(20, 48, 380, 90) });
                Button now = new Button { Text = "UPDATE NOW", DialogResult = DialogResult.Yes, Bounds = new Rectangle(20, 150, 190, 40), BackColor = Accent, ForeColor = Color.Black, FlatStyle = FlatStyle.Flat, Font = new Font("Segoe UI", 9.5f, FontStyle.Bold) };
                Button later = new Button { Text = "PLAY CURRENT VERSION", DialogResult = DialogResult.No, Bounds = new Rectangle(230, 150, 190, 40), BackColor = Panel, ForeColor = Fg, FlatStyle = FlatStyle.Flat, Font = new Font("Segoe UI", 9.5f) };
                f.Controls.Add(now);
                f.Controls.Add(later);
                f.AcceptButton = now;
                f.CancelButton = later;
                if (f.ShowDialog(this) == DialogResult.Yes) InstallUpdate(forJoin);
            }
        }

        void InstallUpdate(bool thenPlay = false)
        {
            if (latest == null || !latest.Available) return;
            Busy(true, "Updating DRBR...");
            Background(() =>
            {
                InstallResult r = C.ApplyUpdate(latest, Progress);
                if (r.LauncherPending && LauncherSwap.Start(P, r.PendingLauncherSha ?? Hash.Sha256File(r.PendingLauncher), Process.GetCurrentProcess().Id, true))
                {
                    Ui(Close);
                    return;
                }
                latest = null;
                Ui(() =>
                {
                    MessageBox.Show(this, "DRBR " + r.Version + " is installed." + (r.Notes.Count > 0 ? "\n\n" + string.Join("\n", r.Notes.ToArray()) : ""), "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    if (thenPlay) Play();
                });
            });
        }

        void Play()
        {
            Busy(true, "Starting DRBR...");
            Background(() =>
            {
                PlayResult pr;
                try { pr = C.Play(t => Ui(() => lblStatus.Text = t), 120); }
                catch (DrbrException e) when (e.Code == "needs_repair")
                {
                    bool yes = false;
                    Ui(() => yes = MessageBox.Show(this, e.Message + "\n\nRepair it now? (Your saves and settings are kept.)", "DRBR", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes);
                    Thread.Sleep(50);
                    if (!yes) return;
                    C.Repair(Progress);
                    pr = C.Play(t => Ui(() => lblStatus.Text = t), 120);
                }
                if (pr.StartResult == "error") Ui(() => MessageBox.Show(this, "DRBR could not start: " + pr.Error + "\n\nUse REPAIR, then try again.", "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Warning));
                if (pr.Game != null)
                {
                    Ui(() => WindowState = FormWindowState.Minimized);
                    Thread w = new Thread(() =>
                    {
                        try { pr.Game.WaitForExit(); } catch { }
                        List<string> d = C.AfterGame();
                        Ui(() =>
                        {
                            WindowState = FormWindowState.Normal;
                            lblStatus.Text = d.Count == 0 ? "DRBR closed. Your own DELTARUNE saves were not touched." : "DRBR closed. Note: " + string.Join(", ", d.ToArray());
                            if (C.PendingJoin().Count > 0) CheckUpdates(true, true);
                        });
                    }) { IsBackground = true };
                    w.Start();
                }
            });
        }

        void Repair()
        {
            if (MessageBox.Show(this, "Repair checks every DRBR file and rebuilds anything missing or damaged from DRBR's own package and your DELTARUNE. Your saves and settings are kept.\n\nRepair now?", "DRBR", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            Busy(true, "Repairing DRBR...");
            Background(() =>
            {
                List<string> notes = C.Repair(Progress);
                Ui(() => MessageBox.Show(this, string.Join("\n", notes.ToArray()), "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information));
            });
        }

        void RestoreSave()
        {
            if (MessageBox.Show(this, "RESTORE STARTING SAVE: the next start of DRBR is the provided starting save again (the room before the Roaring Knight).\n\n" +
                                      "Your DRBR story saves are moved to the backups folder (not deleted). Your DRBR settings, skin, SOUL colour, keybinds and your own DELTARUNE saves are not touched.\n\nRestore now?",
                                "DRBR", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            Busy(true, "Restoring the starting save...");
            Background(() =>
            {
                Manifest m = C.InstalledManifest();
                if (m != null) SaveProfile.EnsureBundle(P, m.SaveProfile, C.Settings.StartMode);
                int n = SaveProfile.RestoreStartingSave(P);
                Ui(() => MessageBox.Show(this, "Done. The next start is the provided starting save" + (n > 0 ? " (" + n + " DRBR save file(s) moved to backups)." : "."), "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information));
            });
        }

        void ShowNotes()
        {
            string notes = "";
            try
            {
                if (latest != null && latest.Available) notes = "NEW: DRBR " + latest.Manifest.Version + "\n" + latest.Manifest.Notes + "\n\n";
                Manifest m = C.InstalledManifest();
                if (m != null) notes += "INSTALLED: DRBR " + m.Version + "\n" + m.Notes;
            }
            catch { }
            if (notes.Trim().Length == 0) notes = "No release notes are installed.";
            using (Form f = new Form { Text = "DRBR release notes", ClientSize = new Size(560, 420), StartPosition = FormStartPosition.CenterParent, BackColor = Bg, ForeColor = Fg, Font = Font })
            {
                TextBox tb = new TextBox { Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill, Text = notes.Replace("\n", "\r\n"), BackColor = Panel, ForeColor = Fg, BorderStyle = BorderStyle.None };
                f.Controls.Add(tb);
                if (BuildInfo.UpdatesConfigured)
                {
                    LinkLabel l = new LinkLabel { Text = "All releases on GitHub", Dock = DockStyle.Bottom, LinkColor = Accent, TextAlign = ContentAlignment.MiddleCenter, Height = 28 };
                    l.LinkClicked += (s, e) => { try { Process.Start("https://github.com/" + BuildInfo.GitHubOwner + "/" + BuildInfo.GitHubRepo + "/releases"); } catch { } };
                    f.Controls.Add(l);
                }
                f.ShowDialog(this);
            }
        }

        void OpenSettings()
        {
            using (Form f = new Form { Text = "DRBR settings", ClientSize = new Size(500, 330), FormBorderStyle = FormBorderStyle.FixedDialog, StartPosition = FormStartPosition.CenterParent, BackColor = Bg, ForeColor = Fg, Font = Font, MaximizeBox = false, MinimizeBox = false })
            {
                f.Controls.Add(new Label { Text = "When DRBR starts", Font = new Font("Segoe UI", 11f, FontStyle.Bold), ForeColor = Accent, Bounds = new Rectangle(20, 14, 460, 24) });
                RadioButton tpl = new RadioButton { Text = "Start from the DRBR starting save every time (recommended)", Bounds = new Rectangle(20, 42, 460, 24), Checked = C.Settings.StartMode != SaveProfile.ModeContinue };
                RadioButton cont = new RadioButton { Text = "Continue from my last DRBR save (falls back to the starting save)", Bounds = new Rectangle(20, 68, 460, 24), Checked = C.Settings.StartMode == SaveProfile.ModeContinue };
                CheckBox upd = new CheckBox { Text = "Check for updates when DRBR Launcher opens", Bounds = new Rectangle(20, 104, 460, 24), Checked = C.Settings.CheckUpdatesOnStart };
                f.Controls.Add(tpl); f.Controls.Add(cont); f.Controls.Add(upd);
                f.Controls.Add(new Label { Text = "Made from: " + (string.IsNullOrEmpty(C.Settings.GameSource) ? "-" : C.Settings.GameSource) + "\nDRBR folder: " + P.Root + "\nDRBR saves: " + P.LiveProfile, ForeColor = Dim, Bounds = new Rectangle(20, 136, 460, 70) });
                Button saves = new Button { Text = "Open the save folder", Bounds = new Rectangle(20, 212, 200, 32), FlatStyle = FlatStyle.Flat, BackColor = Panel, ForeColor = Fg };
                saves.Click += (s, e) => { try { Directory.CreateDirectory(P.LiveProfile); Process.Start("explorer.exe", "\"" + P.LiveProfile + "\""); } catch { } };
                Button un = new Button { Text = "Uninstall DRBR...", Bounds = new Rectangle(260, 212, 200, 32), FlatStyle = FlatStyle.Flat, BackColor = Panel, ForeColor = Fg };
                un.Click += (s, e) => { f.DialogResult = DialogResult.Abort; f.Close(); };
                Button ok = new Button { Text = "Save", DialogResult = DialogResult.OK, Bounds = new Rectangle(260, 276, 100, 36), BackColor = Accent, ForeColor = Color.Black, FlatStyle = FlatStyle.Flat };
                Button cancel = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Bounds = new Rectangle(370, 276, 100, 36), BackColor = Panel, ForeColor = Fg, FlatStyle = FlatStyle.Flat };
                f.Controls.Add(saves); f.Controls.Add(un); f.Controls.Add(ok); f.Controls.Add(cancel);
                f.AcceptButton = ok; f.CancelButton = cancel;
                DialogResult r = f.ShowDialog(this);
                if (r == DialogResult.Abort) { Uninstall(); return; }
                if (r != DialogResult.OK) return;
                C.Settings.StartMode = cont.Checked ? SaveProfile.ModeContinue : SaveProfile.ModeTemplate;
                C.Settings.CheckUpdatesOnStart = upd.Checked;
                C.Settings.Save(P);
                try
                {
                    Manifest m = C.InstalledManifest();
                    if (m != null) SaveProfile.EnsureBundle(P, m.SaveProfile, C.Settings.StartMode);
                }
                catch (Exception e) { Log.Warn(e.Message); }
                Refresh2();
            }
        }

        void Uninstall()
        {
            if (MessageBox.Show(this, "Uninstall DRBR?\n\nThis removes DRBR's folder (" + P.Root + "), its shortcuts and its Apps entry. Your DELTARUNE in Steam and all your own DELTARUNE saves are not touched.",
                                "Uninstall DRBR", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            bool saves = MessageBox.Show(this, "Also delete the DRBR story saves (" + P.LiveProfile + ")?\n\nChoose No to keep them (they are small and are used again if you reinstall). Your DRBR online settings (skin, SOUL colour, keybinds) always stay.",
                                         "Uninstall DRBR", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes;
            string exe = Application.ExecutablePath;
            C.Engine.Uninstall(saves, exe);
            // this program cannot delete itself while it runs: a short command removes it and the empty folder afterwards
            try
            {
                // (only DRBR's own leftovers: the launcher, its logs folder, then the folder itself only if it is empty)
                Process.Start(new ProcessStartInfo("cmd.exe", "/c ping 127.0.0.1 -n 3 > nul & del /f /q \"" + exe + "\" & rmdir /s /q \"" + P.LogDir + "\" 2>nul & rmdir /q \"" + P.Root + "\" 2>nul")
                { CreateNoWindow = true, UseShellExecute = false });
            }
            catch { }
            MessageBox.Show(this, "DRBR was uninstalled.", "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Close();
        }
    }
}
