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
echo "Command: $command <BR>";
$context = new ZMQContext();
$requester = new ZMQSocket($context, ZMQ::SOCKET_DEALER);
$requester->connect("ipc:///run/cmdsrv_sock");
$requester->send($command);
$reply = $requester->recv();

echo "message: <BR>$reply";
echo "<BR>";
echo strToHex($reply);

function strToHex($string){
    $hex='';
    for ($i=0; $i < strlen($string); $i++){
        $hex .= dechex(ord($string[$i]));
    }
    return $hex;
}
?>
  </body>
</html>