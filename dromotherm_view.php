<?php
    global $path;
    $root = "{$path}dromotherm/";
?>
<style>
pre {
    width:100%;
    height:400px;
    margin:0px;
    padding:0px;
    color:#fff;
    background-color:#300a24;
    overflow: scroll;
    overflow-x: hidden;
    font-size:12px;
}
</style>

<div style="padding:20px">

    <h2>dromotherm</h2>
    Numéro du flux à interroger : <input type="text" id="nb"><br>
    <button class="btn btn-warning" id="learn">learn</button><br><br>
    <div id="pompe"></div>
    <br><br><br>
    <button class="btn btn-warning" id="dromoupdate">mettre à jour dromotherm.py</button><br><br> 
    
</div>
<script>
var root = "<?php echo $root; ?>";
var nb = "";
$("#learn").click(function(){
    nb = $("#nb").val();
    $.ajax({
        url: root+"/read/"+nb,
        dataType: 'json',
        async: true,
        success: function(data) {
            //console.log(data);
            $("#pompe").html(data.join("<br>"));
        }
    });
});

$("#dromoupdate").click(function(){
    $.ajax({
      dataType: 'text',
      url: root+"/dromoupdate",
      async: true,
      success: function(data){
          alert(data);
      }
    });
});

</script>
