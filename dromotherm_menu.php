<?php

    global $session;

    if ($session["write"]) {

        $menu["dromotherm"] = array("name"=>"dromotherm", "order"=>3, "icon"=>"bullhorn", "default"=>"dromotherm",  "l2"=>array());

        $menu["dromotherm"]['l2']["help"] = array(
            "name"=>"API help",
            "href"=>"dromotherm/apihelp",
            "icon"=>"input",
            "order"=>1
        );

        $menu["dromotherm"]['l2']["view"] = array(
            "name"=>"view",
            "href"=>"dromotherm",
            "icon"=>"show_chart",
            "order"=>2
        );
   }
