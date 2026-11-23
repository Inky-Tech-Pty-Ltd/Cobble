<p align="right">
  <img
    src="docs/assets/cobble-logo.png"
    alt="Cobble logo"
    width="130"
  />
</p>


# Cobble
Cobble is an Inky Tech project.

**Inky Tech Pty Ltd**   
Infrastructure of memory.

_Memory is the masterpiece.  
Intelligence is paint._

## The application

Cobble is an app designed to cobble together an entity from information sources and intelligence sources. One of its aims is sovereignty, so that the information is held and backed up in locations that are controlled by the user. The sources of intelligence are modular and pluggable, reducing the dependency on any single supplier.

The centrepiece of the app is a 'room', which draws its inspiration and much of its language from a meeting room.

A room is created by a convenor, who appoints a chair, tables an agenda, and invites participants. The chair is an 'expert system' intelligence that brings a set of standing orders. The convenor can accept those standing orders as-is, or make changes to them if required. The contributions of all participants are 'tabled'. The information on the table acts as context for the ongoing discussion. The convenor controls the permissions and audience of the information that is tabled initially, but the intelligences have to use judgement about information that is tabled _subsequently_.

One of the functions of the standing orders is to create a process so that the meeting can speak with a single voice. In other words, the meeting can 'make decisions'. The process of achieving a single voice might enforce a strict hierarchy between the intelligences at the table, or it might implement something more democratic — different chairs can have different approaches.

All seats at the table are occupied by intelligences. These can be human or AI ... but a third possibility emerges: Because a room speaks with a single voice, a room is _also_ an intelligence. A room (in the person of its chair) can be invited to take a seat in another room.

This creates a different view of the cobbled-together entity. In one sense the entity is cobbled together from intelligences and information sources. In a different sense it is cobbled together out of rooms.

A natural observation is that we can scale up this entity. We can create a department out of rooms, and an organisation out of departments.

It is the intention of the project that the 'room' concept should also scale down. The room has multiple input streams, code on the table, and a single output stream. The room is a program. It is modular.

At even smaller scales we notice that the architecture of a room is uncannily similar to that of a neuron: a set of inputs, a tiny scrap of code and the occasional whack of electricity on a single channel output.

Convenors care about the economics of a room. They want results *at a price*. This creates markets for intelligences, for chairs and for rooms (including their bootstrap code that is on the table at the creation of a new room). In the operation of a meeting, the intelligences continually table new code. A good chair will have rules to manage this code. These rules could be maximalist along the lines of Git, or they could be minimalist along the lines of a meeting output that is stripped back to agenda and minutes only. Or anything in between.

As it stands in November 2026, the app can connect three LLM 'intelligences', Claude, ChatGPT and Mistral. On our test server, for information sources, the app is connected to two filesystems, six GitHub repos and an archive of chat with GPT.

The app makes a distinction between this external data and the data that has been internalised into the entity. The external data is labelled 'sensory' ... it is a taste of the outside world. It is voluminous, multiply redundant, and much of it is not particularly salient. This information has to be ingested by expert systems — rooms — that are under economic pressure to leave a salient representation of it 'on the table'. We are calling this internalised data *memory*. As the app matures, we hope to add 'sensory' sources — email, databases, social media ... and also a browser and search engine so that the entity can turn its senses toward an object of interest.

## Sister project, governance

The project intersects with its sister-repo [Village Link](https://github.com/Inky-Tech-Pty-Ltd/VillageLink) at the point of the *reputations* of the intelligences, chairs, convenors, and rooms. At the boundary of each room is a notional membrane, where opportunity and risk must be assessed. Village Link proposes that a *star credential* might be an effective way of creating a bundle of reputational evidence, and proposes a future *Trust Engine* as the process for assessing that evidence. 

The two projects together pose a hypothesis to be tested: Can we observe normative institutions as emergent structures arising from the interactions of markets and reputation? Can we observe *governance*?

## Value proposition

1. Sovereignty. Reduced vulnerability to the loss of any single intelligence, AI or human.
1. Context, ownership. Layered stores of information 'on the table' and 'in the senses', all controlled by the user.
1. Workspaces, coherence. Each AI voice available to two or more people, all with the shared context of a meeting room.
1. Evolvability, modularity. A mature Cobble will ship with a default set of rooms. (For example for the ingestion of email, the optimisation of tabled code, or the deployment of a trust engine.) Any of these may be swapped-out for something better.
1. Governance? Resource pressure as an organising principle. Rooms, chairs and intelligences selected on reputation. 'Natural' data permission _in the room_.

