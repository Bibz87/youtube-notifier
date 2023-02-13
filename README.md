# YouTube Notifier

On August 13th, 2020, YouTube removed the video upload email notification feature. This script exists to mimick that feature and somewhat bring it back to life.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Python 3.8
  - See [requirements.txt](requirements.txt) for a list of required Python modules
- MongoDB connection string
- [Google OAuth 2.0 Credentials](./Google%20Credentials%20Generation.md)

### Installing

1. Install Python dependencies: `pip install -r requirements.txt`
2. Generate [Google Credentials](./Google%20Credentials%20Generation.md)
3. Put your MongoDB connection string in `./credentials/mongo-connection-string.txt`

## Deployment

The Notifier was developed to be deployed on a Google Cloud Function but it can run locally or (in theory) on any platform that supports Python 3.8. To deploy on gcloud, use this command: `gcloud functions deploy youtube-notifier --entry-point execute`

## Known Issues

* Videos published close to script run time will not trigger a notification email
* Livestreams are interpreted as regular videos
* Premiered videos are interpreted as already available videos

## Limitations

* Single user support
* All subscriptions will send email notifications regardless of bell status
* Supported languages: English

## Built With

* [VSCode](https://code.visualstudio.com/) - IDE

## Contributing

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## Authors

* **Yannik Beaulieu** - [Bibz87](https://github.com/Bibz87)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Thanks to Billie Thompson ([PurpleBooth](https://github.com/PurpleBooth)) for the [README](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2) and [CONTRIBUTING](https://gist.github.com/PurpleBooth/b24679402957c63ec426) templates
