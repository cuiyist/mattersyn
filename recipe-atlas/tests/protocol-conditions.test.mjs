import test from 'node:test';
import assert from 'node:assert/strict';
import {matchProtocolCondition} from '../static/protocol-conditions.mjs';

test('room-temperature degassing duration is not a temperature',()=>{
 const entries=[['room_temperature_degas_duration',{value:15,unit:'min'}],['nitrogen_backfill_duration',{value:15,unit:'min'}]];
 assert.equal(matchProtocolCondition(entries,'temperature'),undefined);
 assert.equal(matchProtocolCondition(entries,'duration|time')?.[0],'room_temperature_degas_duration');
});
test('temperature selection retains a later actual temperature and its bounds',()=>{
 const temperature={value:null,minimum:170,maximum:280,unit:'degC'};
 const entries=[['room_temperature_degas_duration',{value:15,unit:'min'}],['reaction_temperature',temperature]];
 assert.equal(matchProtocolCondition(entries,'temperature')?.[1],temperature);
});
test('temperature ramps and pressure hold times are not absolute conditions',()=>{
 assert.equal(matchProtocolCondition([['temperature_ramp_rate',{value:5,unit:'degC/min'}]],'temperature'),undefined);
 assert.equal(matchProtocolCondition([['pressure_hold_duration',{value:10,unit:'min'}]],'pressure'),undefined);
});
test('unknown temperature remains unknown and is not replaced by a nearby time',()=>{
 const unknown={value:null,unit:'degC',status:'not_reported'};
 assert.equal(matchProtocolCondition([['temperature',unknown],['duration',{value:10,unit:'min'}]],'temperature')?.[1],unknown);
});
