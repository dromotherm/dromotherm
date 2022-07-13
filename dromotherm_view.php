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
    <div>
      Numéro du flux à interroger : <input type="text" id="nb">
      <br>
      <button class="btn btn-warning" id="learn">learn</button>
      <br><br>
    </div>
    <div id="pompe"></div>
    <br><br><br>
    <div>
      <button class="btn btn-warning" id="dromoupdate">mettre à jour</button>
      <br><br>
      Télécharge la dernière version de dromotherm.py depuis <a href=https://github.com/dromotherm/dromotherm>https://github.com/dromotherm/dromotherm</a>
      <br>
    </div>
    <div>
      **A NOTER :** 
      <br>Un zip des datas est sauvegardé tous les jours sur github : <a href=https://github.com/dromotherm/fieldsave/actions>https://github.com/dromotherm/fieldsave/actions</a>
      <br><br>pour le télécharger :
      <br>1) on clique sur le workflow "download backup", 
      <br>2) on choisit le run le plus récent en date,
      <br>3) on télécharge l'artifact qui doit être nommé dromotherm_backup  
    </div>
    
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
