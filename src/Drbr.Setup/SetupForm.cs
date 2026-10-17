// DRBR-Setup's window: one screen - DELTARUNE FOUND / Installation: Compatible / DRBR Starting Save: Pre-Roaring Knight Room /
// [ INSTALL DRBR ] / Advanced Options.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace Drbr
{
    sealed class SetupForm : Form
    {
        static readonly Color Bg = Color.Black, Fg = Color.White, Accent = Color.FromArgb(255, 213, 0), Dim = Color.FromArgb(150, 150, 150), Panel = Color.FromArgb(24, 24, 32), Bad = Color.FromArgb(255, 110, 110);
        DrbrPaths P;
        readonly Dictionary<string, string> A;
        readonly Label lblFound = new Label(), lblCompat = new Label(), lblSave = new Label(), lblNotes = new Label(), lblStatus = new Label();
        readonly Button btnInstall = new Button(), btnBrowse = new Button(), btnPlay = new Button(), btnClose = new Button();
        readonly LinkLabel lnkAdvanced = new LinkLabel();
        readonly Panel adv = new Panel();
        readonly TextBox txtDir = new TextBox();
        readonly RadioButton rbTemplate = new RadioButton(), rbContinue = new RadioButton();
        readonly CheckBox cbShortcuts = new CheckBox();
        readonly ProgressBar bar = new ProgressBar();
        string payloadDir, tempDir, gameDir;
        Manifest man;
        GameReport report;

        public SetupForm(DrbrPaths p, Dictionary<string, string> a)
        {
            P = p;
            A = a;
            AutoScaleDimensions = new SizeF(96F, 96F);
            AutoScaleMode = AutoScaleMode.Dpi;
            Text = "DRBR Setup";
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(560, 430);
            BackColor = Bg;
            ForeColor = Fg;
            Font = new Font("Segoe UI", 10f);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

            Controls.Add(new Label { Text = "DRBR", Font = new Font("Segoe UI", 34f, FontStyle.Bold), AutoSize = false, TextAlign = ContentAlignment.MiddleCenter, Bounds = new Rectangle(0, 12, 560, 60) });
            Controls.Add(new Label { Text = "DELTARUNE BATTLE ROYALE", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Accent, AutoSize = false, TextAlign = ContentAlignment.MiddleCenter, Bounds = new Rectangle(0, 72, 560, 24) });

            Panel info = new Panel { Bounds = new Rectangle(30, 108, 500, 112), BackColor = Panel };
            lblFound.Bounds = new Rectangle(14, 8, 360, 26); lblFound.Font = new Font("Segoe UI", 11f, FontStyle.Bold);
            lblCompat.Bounds = new Rectangle(14, 36, 470, 22);
            lblSave.Bounds = new Rectangle(14, 60, 470, 22);
            lblNotes.Bounds = new Rectangle(14, 84, 470, 24); lblNotes.ForeColor = Dim; lblNotes.Font = new Font("Segoe UI", 8.5f); lblNotes.AutoEllipsis = true;
            btnBrowse.Text = "Browse..."; btnBrowse.Bounds = new Rectangle(386, 8, 100, 28); btnBrowse.FlatStyle = FlatStyle.Flat; btnBrowse.BackColor = Bg; btnBrowse.ForeColor = Fg;
            btnBrowse.Click += (s, e) => Browse();
            foreach (Control c in new Control[] { lblFound, lblCompat, lblSave, lblNotes, btnBrowse }) info.Controls.Add(c);
            Controls.Add(info);

            btnInstall.Text = "INSTALL DRBR"; btnInstall.Bounds = new Rectangle(130, 232, 300, 56); btnInstall.FlatStyle = FlatStyle.Flat; btnInstall.BackColor = Accent; btnInstall.ForeColor = Color.Black;
            btnInstall.Font = new Font("Segoe UI", 16f, FontStyle.Bold); btnInstall.FlatAppearance.BorderSize = 0; btnInstall.Enabled = false;
            btnInstall.Click += (s, e) => Install();
            Controls.Add(btnInstall);
            btnPlay.Text = "PLAY DRBR"; btnPlay.Bounds = btnInstall.Bounds; btnPlay.FlatStyle = FlatStyle.Flat; btnPlay.BackColor = Accent; btnPlay.ForeColor = Color.Black;
            btnPlay.Font = btnInstall.Font; btnPlay.FlatAppearance.BorderSize = 0; btnPlay.Visible = false;
            btnPlay.Click += (s, e) => PlayNow();
            Controls.Add(btnPlay);

            lnkAdvanced.Text = "Advanced Options"; lnkAdvanced.LinkColor = Dim; lnkAdvanced.Bounds = new Rectangle(30, 298, 200, 22);
            lnkAdvanced.LinkClicked += (s, e) => { adv.Visible = !adv.Visible; };
            Controls.Add(lnkAdvanced);
            adv.Bounds = new Rectangle(30, 320, 500, 76); adv.BackColor = Panel; adv.Visible = false;
            adv.Controls.Add(new Label { Text = "Install to:", Bounds = new Rectangle(10, 8, 80, 22) });
            txtDir.Bounds = new Rectangle(90, 6, 400, 24); txtDir.Text = P.Root; txtDir.BackColor = Bg; txtDir.ForeColor = Fg;
            adv.Controls.Add(txtDir);
            rbTemplate.Text = "Start every launch from the starting save"; rbTemplate.Bounds = new Rectangle(10, 32, 290, 22); rbTemplate.Checked = true;
            rbContinue.Text = "Continue my last DRBR save"; rbContinue.Bounds = new Rectangle(300, 32, 200, 22);
            cbShortcuts.Text = "Desktop and Start menu shortcuts"; cbShortcuts.Bounds = new Rectangle(10, 52, 300, 22); cbShortcuts.Checked = true;
            adv.Controls.Add(rbTemplate); adv.Controls.Add(rbContinue); adv.Controls.Add(cbShortcuts);
            Controls.Add(adv);

            bar.Bounds = new Rectangle(30, 330, 500, 14); bar.Visible = false;
            Controls.Add(bar);
            lblStatus.Bounds = new Rectangle(30, 348, 500, 44); lblStatus.ForeColor = Dim; lblStatus.Font = new Font("Segoe UI", 8.5f);
            Controls.Add(lblStatus);
            btnClose.Text = "Close"; btnClose.Bounds = new Rectangle(430, 394, 100, 30); btnClose.FlatStyle = FlatStyle.Flat; btnClose.BackColor = Panel; btnClose.ForeColor = Fg;
            btnClose.Click += (s, e) => Close();
            Controls.Add(btnClose);
            Shown += (s, e) => Begin();
            FormClosed += (s, e) => { if (tempDir != null) { try { Fs.DeleteDir(tempDir); } catch { } } };
        }

        void Ui(Action a)
        {
            if (IsDisposed) return;
            try { if (InvokeRequired) BeginInvoke(a); else a(); } catch { }
        }

        void Begin()
        {
            lblFound.Text = "Looking for DELTARUNE...";
            Thread t = new Thread(() =>
            {
                try
                {
                    payloadDir = Payload.Extract(P, out tempDir);
                    man = InstallEngine.VerifyPayload(payloadDir, null);
                    string g = A.ContainsKey("game") ? A["game"] : null;
                    if (g == null) foreach (string c in GameLocator.Candidates()) { g = c; break; }
                    Ui(() => Inspect(g));
                }
                catch (Exception e) { Ui(() => { lblFound.Text = "DRBR Setup cannot continue"; lblFound.ForeColor = Bad; lblCompat.Text = e.Message; }); Log.Error(e.ToString()); }
            }) { IsBackground = true };
            t.Start();
        }

        void Inspect(string g)
        {
            gameDir = g;
            if (g == null)
            {
                lblFound.Text = "DELTARUNE NOT FOUND";
                lblFound.ForeColor = Bad;
                lblCompat.Text = "Click Browse... and pick your DELTARUNE folder (the one with DELTARUNE.exe).";
                lblSave.Text = "DRBR Starting Save: Pre-Roaring Knight Room";
                btnInstall.Enabled = false;
                return;
            }
            lblFound.Text = "Checking DELTARUNE...";
            Thread t = new Thread(() =>
            {
                GameReport r = GameCheck.Inspect(g, man.SupportedGameBuilds);
                Ui(() =>
                {
                    report = r;
                    lblFound.Text = r.Found ? "DELTARUNE FOUND" : "DELTARUNE NOT FOUND";
                    lblFound.ForeColor = r.Found ? Fg : Bad;
                    lblCompat.Text = r.Compatible ? "Installation: Compatible" + (r.Build != null ? " (" + r.Build.Name + ")" : "") : "Installation: " + r.Summary;
                    lblCompat.ForeColor = r.Compatible ? Fg : Bad;
                    lblSave.Text = "DRBR Starting Save: Pre-Roaring Knight Room";
                    // the folder that was found, and every note in full under the button (one line here was cut off)
                    lblNotes.Text = g;
                    new ToolTip().SetToolTip(lblNotes, g);
                    lblStatus.Text = r.Notes.Count > 0 ? string.Join(" ", r.Notes.ToArray()) : "";
                    btnInstall.Enabled = r.Compatible;
                    if (File.Exists(P.StateFile)) btnInstall.Text = "REINSTALL DRBR";
                });
            }) { IsBackground = true };
            t.Start();
        }

        void Browse()
        {
            using (FolderBrowserDialog d = new FolderBrowserDialog { Description = "Pick your DELTARUNE folder (the one with DELTARUNE.exe)" })
            {
                if (d.ShowDialog(this) == DialogResult.OK) Inspect(d.SelectedPath);
            }
        }

        void Install()
        {
            string root;
            try { root = SetupProgram.DrbrFolder(txtDir.Text.Trim()); }
            catch { MessageBox.Show(this, "That install folder is not valid.", "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
            if (!string.Equals(root, P.Root, StringComparison.OrdinalIgnoreCase))
            {
                P = new DrbrPaths(root);
                Log.Open(P.LogDir, "DRBR Setup");
            }
            btnInstall.Enabled = false; btnBrowse.Enabled = false; lnkAdvanced.Enabled = false; adv.Visible = false; btnClose.Enabled = false;
            bar.Visible = true;
            string mode = rbContinue.Checked ? SaveProfile.ModeContinue : SaveProfile.ModeTemplate;
            bool shortcuts = cbShortcuts.Checked;
            Thread t = new Thread(() =>
            {
                try
                {
                    InstallResult r = new InstallEngine(P).Install(new InstallOptions
                    {
                        GameDir = gameDir,
                        PayloadDir = payloadDir,
                        StartMode = mode,
                        Shortcuts = shortcuts,
                        Operation = File.Exists(P.StateFile) ? "reinstall" : "install",
                        Progress = (text, pct) => Ui(() => { bar.Value = Math.Max(0, Math.Min(100, pct)); lblStatus.Text = text; })
                    });
                    // the starting profile, validated once more as the launcher will see it
                    SaveProfile.EnsureBundle(P, man.SaveProfile, mode);
                    string bad = new InstallEngine(P).VerifyInstall(true);
                    if (bad != null) throw new DrbrException("verify", bad);
                    Ui(() =>
                    {
                        lblFound.Text = "DRBR " + r.Version + " IS INSTALLED";
                        lblCompat.Text = "Your DELTARUNE in Steam and your saves were not changed.";
                        lblSave.Text = "DRBR Starting Save: Pre-Roaring Knight Room (ready)";
                        lblStatus.Text = r.Notes.Count > 0 ? string.Join(" ", r.Notes.ToArray()) : "Installed to " + P.Root;
                        bar.Visible = false;
                        btnBrowse.Visible = false;
                        lnkAdvanced.Visible = false;
                        btnInstall.Visible = false;
                        btnPlay.Visible = true;
                        btnClose.Enabled = true;
                    });
                }
                catch (Exception e)
                {
                    Log.Error(e.ToString());
                    Ui(() =>
                    {
                        bar.Visible = false;
                        lblStatus.Text = "Log: " + (Log.FilePath ?? "");
                        MessageBox.Show(this, e.Message, "DRBR Setup", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        btnInstall.Enabled = report != null && report.Compatible; btnBrowse.Enabled = true; lnkAdvanced.Enabled = true; btnClose.Enabled = true;
                    });
                }
            }) { IsBackground = true };
            t.Start();
        }

        void PlayNow()
        {
            try
            {
                Process.Start(new ProcessStartInfo(P.LauncherExe, "--autoplay") { UseShellExecute = false, WorkingDirectory = P.Root });
                Close();
            }
            catch (Exception e) { MessageBox.Show(this, "DRBR Launcher could not be started: " + e.Message, "DRBR", MessageBoxButtons.OK, MessageBoxIcon.Warning); }
        }
    }
}
