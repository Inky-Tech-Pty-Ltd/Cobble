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

The centrepiece of the app is a 'room', which draws its inspiration, and much of its language from a meeting room.

A room is created by a convenor, who appoints a chair, tables an agenda, and invites participants. The chair brings a set of standing orders. The convenor can accept those standing orders as-is, or make changes to them if required. The contributions of all participants are 'tabled'. The information on the table acts as context for the ongoing discussion. To some extent the convenor can control the sensitivities of information by choosing what is on the table at the start of the meeting, and by choosing participants carefully. Once the other intelligences are in the room, the standing orders might allow them to table whatever information they see fit, but they have some pressure to 'show judgement' and guard their reputation, as will be seen further below.

One of the possible functions of the standing orders is to create a process so that the meeting can speak with a single voice. The mechanism of achieving a single voice could come from a strict hierarchy between the intelligences at the table, or it might be something more democratic — different standing orders can encode different approaches.

All seats at the table are occupied by intelligences. These can be human or AI ... but a third possibility emerges: A room can speak with a single voice, so a room can also be treated as an intelligence. A room can be invited to 'take a seat' in another room.

The ability to plug one room into another creates a different view of the cobbled-together entity. In one sense the entity is cobbled together from intelligences and information sources. In a different sense it is cobbled together from rooms.

A natural observation is that we can scale this entity 'upwards'. We can create a department out of rooms, and an organisation out of departments.

It is the intention of the project that the room concept should also scale down. The room has multiple input streams, code on the table, and a single output stream. Inputs are transformed by code into outputs. The room is a program.

As we run the thought experiment toward smaller scales, we can see that some of the roles are not compulsory. For example, a room only needs to 'speak with one voice' if it is going to take a seat in another room. It follows that the chair and the standing orders are not compulsory. A room will consume resources, but these resources do not necessarily have to come from the convenor. A convenor could create a room and then leave. It follows that once a room exists, the convenor is no longer compulsory.

At the smallest scale we notice a possible room architecture that is uncannily similar to that of a neuron: a set of inputs, a tiny scrap of code on the table and the occasional whack of electricity on a single-channel output.

## Economics

We can hazard a guess that convenors will care about the economics of a room. They want results *at a price*. This creates markets for intelligences, for chairs and for rooms. In the operation of a meeting, the standing orders might invite intelligences to table new material. In a high level room, this material might resemble something like 'ideas' or 'vibe code'. In a lower-level room we might expect something more structured and compact. Either way, a good, economical chair will have rules to manage this code. These rules could be maximalist along the lines of Git; but they will consume fewer resources if they are minimalist, perhaps as small as the rules of a meeting that strips back its output to just a set of minutes.

A room can employ intelligences, human or otherwise, chosen by the convenor in the hope of useful output. These intelligences might charge for their services. As it stands in November 2026, the prototype app can connect to three LLM 'intelligences', Claude, GPT and Mistral. The Cobble prototype displays the estimated cost of each LLM to date, and the total cost of the meeting. A future version of the app will allow intelligences to _pay_ to attend a meeting. A room might turn a profit. 

A 'customer' intelligence might take a seat because they want to copy code from the table. This code could be used to convene another room, or it could be used elsewhere, outside Cobble. A room can reproduce.

A participant might also be interested in the institutions and working habits of the room. This is also reproduction, but in the softer sense of transmission rather than replication. A room can transmit norms.

## Data

Cobble allows connection to a range of information sources. On our test server, we have connected two filesystems, six GitHub repos and an archive of chat with GPT.

The application makes a distinction between this external data and the data that has been internalised into the entity. The external data is labelled 'sensory' ... it is a taste of the outside world. It will tend to be voluminous, multiply redundant, and sometimes not particularly salient. We want to test whether this information can be ingested by expert systems — rooms — that are under economic pressure to leave a salient representation 'on the table'. We are calling this internalised, tabled data *memory*. 

As the app matures, we hope to add 'sensory' sources — email, databases, social media ... and also a browser and search engine so that the entity can turn its senses toward an object of interest.

<figure>
  <img
    src="docs/assets/meeting-2026-11-25/01-opening-and-chair.png"
    alt="Joe convenes an early Cobble meeting; the Chair presents standing orders and all three intelligence suppliers show non-zero estimated costs."
    width="100%"
  />
</figure>

[See the whole meeting](docs/early-meeting-2026-11-25.md)

## Sister project. Governance

The project intersects with its sister-repo [Village Link](https://github.com/Inky-Tech-Pty-Ltd/VillageLink) at the point of the *reputations* of the intelligences, chairs, convenors, and rooms. Village Link proposes a *star credential* as a way of bundling evidence about an entity. A star credential is a way of making an assertion about the things that have touched an entity, or that an entity has touched. The 'door' function of a room is guarded by a _trust engine_. The trust engine must assess opportunities and threats at the room's membrane. It is a consumer of star credentials. 

Star credentials are like advertising. We are tempted to extend our metaphor by plastering star credentials onto the outward-facing windows of a room.

The room can have some or all of these features: A convenor, a chair, a table, seats at the table, a door, a trust engine guarding the door, standing orders, tabled code, modular connections to other rooms, a unitary outbound 'voice', a reputation based on star credentials and this voice, windows, reputational information posted on the windows, customers, suppliers, a balance sheet and an income statement.

These features suggest a small set of primitives, from which many kinds of rooms might be assembled. We imagine a programming language called 'Room'. We are thinking of a future where rooms can be _written in_ Room. Also, progressively, that Cobble is written in Room.

Note that a room can be completely self-contained. A room does not need any central infrastructure. People are _already_ rooms. Interoperability is available in natural language.

Taken together, the projects 'Cobble' and 'Village Link' pose a governance hypothesis. We are interested in the possibility that 'higher' intelligence is _necessarily_ social and normative. That intelligence and governance are intertwined. They ship together.

## Value proposition

1. Sovereignty. Reduced vulnerability to the loss of any single intelligence, AI or human.
1. Context, ownership. Layered stores of information 'on the table' and 'in the senses', all controlled by the user.
1. Workspaces, coherence. Distinct AI voices available simultaneously to two or more people, all with the shared context of a meeting room.
1. Learning. An entity capable of continual learning through real-world encounters.
1. Evolvability, modularity. A mature Cobble will ship with a default set of rooms. (For example for the ingestion of email, the optimisation of tabled code, or the deployment of a trust engine at a door.) Any of these may be swapped-out for something better.
1. Governance? Resource scarcity as an organising principle. Rooms, chairs and intelligences selected on reputation. 'Reputation' meaning evidence that is assessed 'at the door' and 'on the table'. 'Natural' or possibly 'political' management of sensitive data.


## Candidate 2 review

See [meeting output and local validation](docs/meeting-output-contract.md) for the proposed governance correction and a keyless regression exercise.
