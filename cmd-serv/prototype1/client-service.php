<?php
/*
*  xsce-cmdsrv client
*  Connects DEALER socket to ipc:///run/cmdsrv_sock
*  Sends command, expects response back
*/
?>
<html> 
	<body> 
		<h1>Hello world!</h1> 
		<p>This is being served from xsce-cmdsrv using PHP.</p>

<?php
//  Socket to talk to server
$command = $_GET['command'];
echo $command;
$context = new ZMQContext();
$requester = new ZMQSocket($context, ZMQ::SOCKET_DEALER);
$requester->connect("ipc:///run/cmdsrv_sock");
$requester->send(command);
$reply = $requester->recv();

echo "message: $reply";
?>
  </body>
</html>