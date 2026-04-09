<?php
$con=mysqli_connect("localhost","root","","bdreclamation");
$tel=$_POST["tel"];
$genre=$_POST["genre"];
$cat=$_POST["cat"];
$desc=$_POST["desc"];
$req="select * from client;";
$req1="insert into reclamation values(null,'$desc','N',now(),'1970-01-01','$tel','$cat');";
$req2="select * from client where telclt='$tel';";
$res=mysqli_query($con,$req2);
$req3="select * from reclamation r,client c where r.telclt=c.telclt and c.telclt='$tel' and etat='N';";
if (mysqli_num_rows($res)==0)
	die('client non enregistrer');
$res3=mysqli_query($con,$req3);
if (mysqli_num_rows($res3)!=0)
	die('reclamation nest pas traiter');
$res5=mysqli_query($con,$req1);
if($res5)
	echo "client ajuter avec succ";
	
mysqli_close($con);
	
	
?>