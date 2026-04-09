<?php
$con=mysqli_connect("localhost","root","","bdreclamation");
$tel=$_POST["tel"];
$dp=$_POST["daterep"];
$req="select * from reclamation r,client c where r.telclt=c.telclt and c.telclt='$tel' and etat='N';";
$res=mysqli_query($con,$req);
if (mysqli_num_rows($res)==0)
	die('Aucune reclamation nest pas traiter pour ce client');
$req1="update reclamation set etat='O' , daterep='$dp' where etat='N' and telclt='$tel';";
$res1=mysqli_query($con,$req1);
if($res1)
	echo "ressir avex success";
mysqli_close($con);

?>