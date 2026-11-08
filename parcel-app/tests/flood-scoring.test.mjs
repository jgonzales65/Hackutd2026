import test from 'node:test';
import assert from 'node:assert/strict';
import { assessFlood } from '../lib/flood-scoring.ts';
import { level, displayScore } from '../lib/risk.ts';
const match = (zone, subtype, sfha) => ({zone,subtype,sfha,source:'https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28',citation:'test-fixture',retrievedAt:'2026-11-08'});

test('minimal X only scores low with full mapped parcel coverage', () => {
 const matches=[match('X','AREA OF MINIMAL FLOOD HAZARD',false)];
 assert.equal(assessFlood(matches,true,true).score,10);
 assert.equal(assessFlood(matches,true,false).score,null);
});
test('SFHA is high and partial coverage yields a minimum observed severity', () => {
 for(const zone of ['A','AE','AO','AH','AR','A99']) {
  const a=assessFlood([match(zone,null,true)],true,false);
  assert.equal(a.score,65);assert.equal(a.status,'minimum_observed_severity');
 }
});
test('coastal V and floodway receive critical severity; maximum wins', () => {
 assert.equal(assessFlood([match('VE',null,true)],true,true).score,90);
 assert.equal(assessFlood([match('AE','FLOODWAY',true),match('X','AREA OF MINIMAL FLOOD HAZARD',false)],true,true).score,90);
});
test('shaded and future X differ from minimal X', () => {
 for(const subtype of ['0.2 PCT ANNUAL CHANCE FLOOD HAZARD','1 PCT FUTURE CONDITIONS'])
  assert.equal(assessFlood([match('X',subtype,false)],true,false).score,35);
});
test('missing, unknown, and inconsistent evidence never becomes low risk', () => {
 assert.equal(assessFlood([],true,true).score,null);
 assert.equal(assessFlood([],false,false).status,'data_unavailable');
 assert.equal(assessFlood([match('AE',null,true)],false,true).score,null);
 for(const m of [match('D',null,null),match('X',null,false),match('X','AREA OF MINIMAL FLOOD HAZARD',true)])
  assert.equal(assessFlood([m],true,true).score,null);
 assert.equal(assessFlood([match('X','AREA OF MINIMAL FLOOD HAZARD',false),match('D',null,null)],true,true).score,null);
});
test('all classification thresholds match user requirements', () => {
 for(const [score,label] of [[null,'Not assessed'],[0,'Low'],[24,'Low'],[25,'Moderate'],[49,'Moderate'],[50,'High'],[74,'High'],[75,'Critical'],[100,'Critical']])
  assert.equal(level(score).label,label);
});
test('flood display score never changes the overall assessment', () => {
 const parcel={score:null,assessment:assessFlood([match('AE',null,true)],true,false)};
 assert.equal(displayScore(parcel),65);assert.equal(parcel.score,null);
 assert.deepEqual(parcel.assessment.missingCategories,['environmental','financial','ownership/title','permits','zoning']);
});
