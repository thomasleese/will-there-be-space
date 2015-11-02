var irc = require('irc');
var redis = require('redis');

var redisClient = redis.createClient(process.env.REDIS_URI);
var ircClient = new irc.Client(process.env.IRC_SERVER, 'SpaceBot', {
  channels: [process.env.IRC_CHANNEL],
});

redisClient.on('message', function(channel, message) {
  ircClient.say(process.env.IRC_CHANNEL, message);
});

redisClient.subscribe('updates');
