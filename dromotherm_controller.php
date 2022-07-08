<?php

// no direct access
defined('EMONCMS_EXEC') or die('Restricted access');

function dromotherm_controller() {

    global $session, $route, $redis, $path;

    // Default route format
    $route->format = 'json';

    // Result can be passed back at the end or part way in the controller
    $result = false;

    // only for user with API write access
    if (!$session['write']) return false;

    // view the module control panel
    if ($route->action == "view") {
        $route->format = 'html';
        return view("Modules/dromotherm/dromotherm_view.php", array());
    }

    if ($route->action == "apihelp") {
        $route->format = 'html';
        return view("Modules/dromotherm/dromotherm_api_help.php", array());
    }

    //*************************************************************************************************
    // lance un script python pour lire des capteurs
    if ($route->action == "read") {
        $route->format = "json";
        $cmd = "Modules/dromotherm/./hello.py";
        exec($cmd, $res, $retval);
        //exec('whoami', $res, $retval);
        //print_r($res);
        //print($retval);
        return $res;
    }
    
    if ($route->action == "dromoupdate") {
        $route->format = "text";
        $cmd = "wget -O /opt/openenergymonitor/test.py https://raw.githubusercontent.com/dromotherm/sandbox/master/test.py>/dev/null";
        if ($redis->rpush("service-runner",$cmd)) {
            $result= "service-runner trigger for command $cmd";
        } else {
            $result= "could not send trigger";
        }
        return $result;
    }

    // Pass back result
    return array('content' => $result);
}
