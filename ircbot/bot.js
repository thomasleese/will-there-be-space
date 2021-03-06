var irc = require('irc');
var redis = require('redis');

var redisClient = redis.createClient(process.env.REDIS_URL);
var ircClient = new irc.Client(process.env.IRC_SERVER, 'SpaceBot', {
  channels: [process.env.IRC_CHANNEL],
});

redisClient.on('message', function(channel, message) {
  if (process.env.IRC_CHANNEL) {
    ircClient.say(process.env.IRC_CHANNEL, message);
  }
});

redisClient.subscribe('updates');
