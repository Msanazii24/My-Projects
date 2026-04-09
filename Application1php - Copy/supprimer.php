<?php
require("connection.php");
$id=$_POST["id"];
$req="select * from livre where id_liv='$id';";
$req1="delete from livre where id_liv='$id';";
$res=mysqli_query($con,$req);
$nbl=mysqli_num_rows($res);
if ($nbl==0)
	echo "id n'existe pas";
else{
$res1=mysqli_query($con,$req1);
	if (mysqli_affected_rows($con)==0)
		echo " probleme de suppression";
	else {
	echo "supprission avec succes";
	
}
}
mysqli_close($con);

?>