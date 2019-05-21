#include <iostream>
#include "include/twitcurl.h"
#pragma comment(lib,"legacy_stdio_definitions.lib")
#pragma comment(lib,"lib\\twitcurl.lib")
using namespace std;
FILE _iob[] = { *stdin, *stdout, *stderr };

extern "C" FILE * __cdecl __iob_func(void)
{
	return _iob;
}
int main() {
	std::string userName("kotatsua_sup");  //ユーザ名
	std::string passWord("gear1001");  //パスワード

	std::string myConsumerKey("kNePGOncpjWFreJ328eyYohGz");
	std::string myConsumerSecuret("UT1iFpefTYbGfP2xL5hjGCYQnqNUku0XN3MA4Oi14nnc15WI5I");

	std::string myOAuthAccessTokenKey("953817124748738561-fPoMGgUygN8nIoHAGIiXdu6TAn9eJBd");
	std::string myOAuthAccessTokenSecret("XVHphf6VFbXFglpmUom59Vg70FVco7Kpp2R6BTPtS5Ida");

	std::ifstream oAuthTokenKeyIn;
	std::ifstream oAuthTokenSecretIn;

	twitCurl twitterObj;
	std::string tmpStr;
	std::string replyMsg;
	char tmpBuf[1024];

	/* Set twitter username and password */
	twitterObj.setTwitterUsername(userName);
	twitterObj.setTwitterPassword(passWord);

	/* OAuth flow begins */
	twitterObj.getOAuth().setConsumerKey(myConsumerKey);
	twitterObj.getOAuth().setConsumerSecret(myConsumerSecuret);

	/* Step 1: Check if we alredy have OAuth access token from a previous run */
	oAuthTokenKeyIn.open("twitterClient_token_key.txt");
	oAuthTokenSecretIn.open("twitterClient_token_secret.txt");

	memset(tmpBuf, 0, 1024);
	oAuthTokenKeyIn >> tmpBuf;
	myOAuthAccessTokenKey = tmpBuf;

	memset(tmpBuf, 0, 1024);
	oAuthTokenSecretIn >> tmpBuf;
	myOAuthAccessTokenSecret = tmpBuf;

	oAuthTokenKeyIn.close();
	oAuthTokenSecretIn.close();

	if (myOAuthAccessTokenKey.size() && myOAuthAccessTokenSecret.size())
	{
		/* If we already have these keys, then no need to go through auth again */
		printf("\nUsing:\nKey: %s\nSecret: %s\n\n",
			myOAuthAccessTokenKey.c_str(), myOAuthAccessTokenSecret.c_str());

		twitterObj.getOAuth().setOAuthTokenKey(myOAuthAccessTokenKey);
		twitterObj.getOAuth().setOAuthTokenSecret(myOAuthAccessTokenSecret);
	}
	else
	{
		/* Step 2: Get request token key and secret */
		std::string authUrl;
		twitterObj.oAuthRequestToken(authUrl);

		/* Step 3: Get PIN  */
		/* pass auth url to twitCurl and get it via twitCurl PIN handling */
		twitterObj.oAuthHandlePIN(authUrl);

		/* Step 4: Exchange request token with access token */
		twitterObj.oAuthAccessToken();

		/* Step 5: save this access token key and secret for future use */
		twitterObj.getOAuth().getOAuthTokenKey(myOAuthAccessTokenKey);
		twitterObj.getOAuth().getOAuthTokenSecret(myOAuthAccessTokenSecret);

		/* Step 6: Save these keys in a file or wherever */
		std::ofstream oAuthTokenKeyOut;
		std::ofstream oAuthTokenSecretOut;

		oAuthTokenKeyOut.open("twitterClient_token_key.txt");
		oAuthTokenSecretOut.open("twitterClient_token_secret.txt");

		oAuthTokenKeyOut.clear();
		oAuthTokenSecretOut.clear();

		oAuthTokenKeyOut << myOAuthAccessTokenKey.c_str();
		oAuthTokenSecretOut << myOAuthAccessTokenSecret.c_str();

		oAuthTokenKeyOut.close();
		oAuthTokenSecretOut.close();
	}
	/* OAuth flow ends */

	/* Account credentials verification */
	if (twitterObj.accountVerifyCredGet())
	{
		twitterObj.getLastWebResponse(replyMsg);
		printf("\naccountVerifyCredGet web response:\n%s\n", replyMsg.c_str());
	}
	else
	{
		twitterObj.getLastCurlError(replyMsg);
		printf("\naccountVerifyCredGet error:\n%s\n", replyMsg.c_str());
	}

	/* Post a new status message */
	cin >> tmpStr;
	replyMsg = "";
	if (twitterObj.statusUpdate(tmpStr))
	{
		twitterObj.getLastWebResponse(replyMsg);
		printf("\nstatusUpdate web response:\n%s\n", replyMsg.c_str());
	}
	else
	{
		twitterObj.getLastCurlError(replyMsg);
		printf("\nstatusUpdate error:\n%s\n", replyMsg.c_str());
	}

	return 0;
}