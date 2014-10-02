<?php
/*
*  xsce-cmdsrv client
*  Connects REQ socket to ipc:///run/cmdsrv_sock
*  Sends command, expects response back
*/
?>
<html> 
	<body> 
		<h1>Hello world!</h1> 
		<p>This is being served from xsce-cmdsrv using PHP.</p>

<?php
$context = new ZMQContext();
$requester->send("Hello");
$reply = $requester->recv();

echo "message: $reply";
?>
  </body>
</html>